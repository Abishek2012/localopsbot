from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: str = Field(
        min_length=1,
        examples=["conversation-123"]
    )

    message: str = Field(
        min_length=1,
        max_length=5000,
        examples=["How do I reset my access?"]
    )

    request_id: Optional[str] = None


class ChatResponse(BaseModel):
    request_id: str
    job_id: str
    status: str


class FailureModeRequest(BaseModel):
    mode: str


class ActionRequest(BaseModel):
    action_type: str = "create_ticket"

    title: str = Field(
        min_length=1,
        max_length=500
    )

    description: str = Field(
        min_length=1,
        max_length=5000
    )

    idempotency_key: str = Field(
        min_length=1
    )

    simulate_ambiguous_timeout: bool = False


class ActionResponse(BaseModel):
    status: str
    idempotency_key: str
    result: Optional[str] = None
    duplicate: bool = False
    recovered_after_timeout: bool = False