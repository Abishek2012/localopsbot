import uuid

from fastapi import APIRouter, HTTPException

from app.core.database import get_job
from app.core.metrics import CHAT_REQUESTS_TOTAL
from app.models.schemas import (
    ActionRequest,
    ActionResponse,
    ChatRequest,
    ChatResponse,
    FailureModeRequest,
)
from app.services.action import (
    AmbiguousActionTimeout,
    ActionError,
    action_service,
)
from app.services.mock_llm import mock_llm_service
from app.services.queue import (
    create_job,
    queue_service,
)
from app.services.retrieval import retrieval_service


router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(request: ChatRequest):

    request_id = (
        request.request_id
        or str(uuid.uuid4())
    )

    job_id = str(uuid.uuid4())

    job = create_job(
        job_id=job_id,
        conversation_id=request.conversation_id,
        message=request.message,
        request_id=request_id,
    )

    try:
        queue_service.enqueue(job)

        CHAT_REQUESTS_TOTAL.labels(
            status="accepted"
        ).inc()

        return ChatResponse(
            request_id=request_id,
            job_id=job_id,
            status="queued",
        )

    except Exception as exc:

        CHAT_REQUESTS_TOTAL.labels(
            status="failed"
        ).inc()

        raise HTTPException(
            status_code=503,
            detail=f"Queue unavailable: {str(exc)}",
        )


@router.post(
    "/action",
    response_model=ActionResponse,
)
async def execute_action(
    request: ActionRequest,
):

    if request.action_type != "create_ticket":

        raise HTTPException(
            status_code=400,
            detail="Unsupported action type",
        )

    try:

        result = (
            action_service.execute_create_ticket(
                title=request.title,
                description=request.description,
                idempotency_key=(
                    request.idempotency_key
                ),
                simulate_ambiguous_timeout=(
                    request.simulate_ambiguous_timeout
                ),
            )
        )

        return ActionResponse(**result)

    except AmbiguousActionTimeout:

        result = (
            action_service.resolve_ambiguous_timeout(
                request.idempotency_key
            )
        )

        return ActionResponse(**result)

    except ActionError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/test/failure-mode")
async def set_failure_mode(
    request: FailureModeRequest,
):

    valid_modes = {
        "success",
        "slow",
        "timeout",
        "rate_limited",
        "server_error",
        "malformed_response",
        "retrieval_error",
    }

    if request.mode not in valid_modes:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid failure mode: "
                f"{request.mode}"
            ),
        )

    try:

        # Store centrally in Redis.
        # Both API and Worker containers
        # will read the same failure mode.
        queue_service.set_failure_mode(
            request.mode
        )

        # Update local API instances too.
        if request.mode == "retrieval_error":

            retrieval_service.set_failure_mode(
                "retrieval_error"
            )

            mock_llm_service.set_failure_mode(
                "success"
            )

        else:

            retrieval_service.set_failure_mode(
                "success"
            )

            mock_llm_service.set_failure_mode(
                request.mode
            )

        return {
            "status": "updated",
            "failure_mode": request.mode,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                f"Unable to update failure mode: "
                f"{str(exc)}"
            ),
        )


@router.get("/readyz")
async def readyz():

    redis_ready = (
        queue_service.is_healthy()
    )

    if not redis_ready:

        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "redis": "unavailable",
            },
        )

    return {
        "status": "ready",
        "redis": "healthy",
    }


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):

    job = get_job(job_id)

    if job is None:

        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job