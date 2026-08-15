import json
import time
import uuid

from app.core.database import get_connection, now
from app.core.metrics import ACTION_EXECUTIONS_TOTAL


class ActionError(Exception):
    def __init__(
        self,
        message: str,
        category: str = "action_error"
    ):
        super().__init__(message)
        self.category = category


class AmbiguousActionTimeout(ActionError):
    def __init__(self, message: str):
        super().__init__(
            message,
            category="ambiguous_timeout"
        )


class ActionService:

    def get_action(self, idempotency_key: str):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM actions
            WHERE idempotency_key = ?
            """,
            (idempotency_key,)
        )

        row = cursor.fetchone()
        connection.close()

        if row is None:
            return None

        action = dict(row)

        if action["request_payload"]:
            action["request_payload"] = json.loads(
                action["request_payload"]
            )

        return action

    def execute_create_ticket(
        self,
        title: str,
        description: str,
        idempotency_key: str,
        simulate_ambiguous_timeout: bool = False
    ):

        existing_action = self.get_action(
            idempotency_key
        )

        # Duplicate request:
        # Never execute the side effect again.
        if existing_action:

            ACTION_EXECUTIONS_TOTAL.labels(
                status="duplicate"
            ).inc()

            return {
                "status": existing_action["status"],
                "idempotency_key": idempotency_key,
                "result": existing_action["result"],
                "duplicate": True,
            }

        connection = get_connection()
        cursor = connection.cursor()

        request_payload = {
            "title": title,
            "description": description,
        }

        try:

            # Persist intent BEFORE execution.
            # This protects against worker restart and
            # duplicate message delivery.
            cursor.execute(
                """
                INSERT INTO actions (
                    idempotency_key,
                    action_type,
                    request_payload,
                    status,
                    result,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key,
                    "create_ticket",
                    json.dumps(request_payload),
                    "processing",
                    None,
                    now(),
                    now(),
                )
            )

            connection.commit()

            # Simulated side effect.
            ticket_id = (
                "TICKET-"
                + str(uuid.uuid4())[:8].upper()
            )

            result = json.dumps(
                {
                    "ticket_id": ticket_id,
                    "title": title,
                    "status": "created",
                }
            )

            # The side effect is now complete.
            cursor.execute(
                """
                UPDATE actions
                SET
                    status = ?,
                    result = ?,
                    updated_at = ?
                WHERE idempotency_key = ?
                """,
                (
                    "completed",
                    result,
                    now(),
                    idempotency_key,
                )
            )

            connection.commit()

            ACTION_EXECUTIONS_TOTAL.labels(
                status="completed"
            ).inc()

            # Simulate this exact scenario:
            # Action completed successfully, but the caller
            # timed out before receiving the response.
            if simulate_ambiguous_timeout:

                raise AmbiguousActionTimeout(
                    "Action may have completed, "
                    "but response timed out"
                )

            return {
                "status": "completed",
                "idempotency_key": idempotency_key,
                "result": result,
                "duplicate": False,
            }

        finally:
            connection.close()

    def resolve_ambiguous_timeout(
        self,
        idempotency_key: str
    ):

        existing_action = self.get_action(
            idempotency_key
        )

        if existing_action is None:

            raise ActionError(
                "No action state found after timeout"
            )

        # The action already completed.
        # Return its result instead of retrying execution.
        if existing_action["status"] == "completed":

            ACTION_EXECUTIONS_TOTAL.labels(
                status="recovered"
            ).inc()

            return {
                "status": "completed",
                "idempotency_key": idempotency_key,
                "result": existing_action["result"],
                "duplicate": True,
                "recovered_after_timeout": True,
            }

        return {
            "status": existing_action["status"],
            "idempotency_key": idempotency_key,
            "result": existing_action["result"],
            "duplicate": True,
            "recovered_after_timeout": True,
        }


action_service = ActionService()