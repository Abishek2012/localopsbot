import time

from app.core.config import settings
from app.core.metrics import (
    LLM_DURATION,
    LLM_ERRORS_TOTAL
)


class LLMError(Exception):
    def __init__(
        self,
        message: str,
        category: str,
        retryable: bool = True
    ):
        super().__init__(message)

        self.category = category
        self.retryable = retryable


class MockLLMService:

    def __init__(self):
        self.failure_mode = settings.failure_mode

    def set_failure_mode(self, mode: str):
        valid_modes = {
            "success",
            "slow",
            "timeout",
            "rate_limited",
            "server_error",
            "malformed_response"
        }

        if mode not in valid_modes:
            raise ValueError(
                f"Invalid failure mode: {mode}"
            )

        self.failure_mode = mode

    def generate(
        self,
        message: str,
        context: list[dict]
    ) -> dict:

        start_time = time.perf_counter()

        try:

            if self.failure_mode == "slow":
                time.sleep(2)

            elif self.failure_mode == "timeout":
                time.sleep(
                    settings.llm_timeout_seconds + 2
                )

                raise LLMError(
                    "LLM request timed out",
                    "timeout"
                )

            elif self.failure_mode == "rate_limited":
                raise LLMError(
                    "LLM rate limit exceeded",
                    "rate_limited"
                )

            elif self.failure_mode == "server_error":
                raise LLMError(
                    "LLM server returned 500",
                    "server_error"
                )

            elif self.failure_mode == "malformed_response":
                raise LLMError(
                    "LLM returned malformed response",
                    "malformed_response"
                )

            context_text = "\n".join(
                document["content"]
                for document in context
            )

            response = (
                f"Based on the available knowledge: "
                f"{context_text}\n\n"
                f"Your question was: {message}"
            )

            return {
                "response": response,
                "sources": [
                    document["id"]
                    for document in context
                ]
            }

        except LLMError as exc:

            LLM_ERRORS_TOTAL.labels(
                error_category=exc.category
            ).inc()

            raise

        finally:

            LLM_DURATION.observe(
                time.perf_counter() - start_time
            )


mock_llm_service = MockLLMService()