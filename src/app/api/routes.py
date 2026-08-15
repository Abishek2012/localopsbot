import uuid

from fastapi import APIRouter, HTTPException

from app.core.metrics import CHAT_REQUESTS_TOTAL
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    FailureModeRequest
)
from app.services.mock_llm import mock_llm_service
from app.services.queue import (
    create_job,
    queue_service
)


router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse
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
        request_id=request_id
    )

    try:
        queue_service.enqueue(job)

        CHAT_REQUESTS_TOTAL.labels(
            status="accepted"
        ).inc()

        return ChatResponse(
            request_id=request_id,
            job_id=job_id,
            status="queued"
        )

    except Exception as exc:

        CHAT_REQUESTS_TOTAL.labels(
            status="failed"
        ).inc()

        raise HTTPException(
            status_code=503,
            detail=f"Queue unavailable: {str(exc)}"
        )


@router.post("/test/failure-mode")
async def set_failure_mode(
    request: FailureModeRequest
):

    try:

        mock_llm_service.set_failure_mode(
            request.mode
        )

        return {
            "status": "updated",
            "failure_mode": request.mode
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@router.get("/readyz")
async def readyz():

    redis_ready = queue_service.is_healthy()

    if not redis_ready:

        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "redis": "unavailable"
            }
        )

    return {
        "status": "ready",
        "redis": "healthy"
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):

    # Database lookup will be implemented
    # with the worker in the next step.

    return {
        "job_id": job_id,
        "status": "pending_implementation"
    }