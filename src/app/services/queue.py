import json
from datetime import datetime, timezone

import redis

from app.core.config import settings


QUEUE_NAME = "chatbot:jobs"
FAILURE_MODE_KEY = "chatbot:failure_mode"


def get_redis_client():
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )


class QueueService:

    def __init__(self):
        self.client = None

    def connect(self):
        self.client = get_redis_client()
        self.client.ping()

    def enqueue(self, job: dict):
        if self.client is None:
            self.connect()

        self.client.rpush(
            QUEUE_NAME,
            json.dumps(job),
        )

    def dequeue(self, timeout: int = 1):
        if self.client is None:
            self.connect()

        result = self.client.blpop(
            QUEUE_NAME,
            timeout=timeout,
        )

        if result is None:
            return None

        _, payload = result

        return json.loads(payload)

    def get_depth(self) -> int:
        if self.client is None:
            self.connect()

        return self.client.llen(QUEUE_NAME)

    def set_failure_mode(self, mode: str):
        if self.client is None:
            self.connect()

        self.client.set(
            FAILURE_MODE_KEY,
            mode,
        )

    def get_failure_mode(self) -> str:
        if self.client is None:
            self.connect()

        mode = self.client.get(
            FAILURE_MODE_KEY
        )

        return mode or "success"

    def is_healthy(self) -> bool:
        try:
            if self.client is None:
                self.connect()

            return self.client.ping()

        except redis.RedisError:
            return False


queue_service = QueueService()


def create_job(
    job_id: str,
    conversation_id: str,
    message: str,
    request_id: str,
) -> dict:

    return {
        "job_id": job_id,
        "conversation_id": conversation_id,
        "message": message,
        "request_id": request_id,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }