import random


RETRYABLE_ERRORS = {
    "timeout",
    "rate_limited",
    "server_error",
    "malformed_response",
    "retrieval_error",
}


def is_retryable(error_category: str) -> bool:
    return error_category in RETRYABLE_ERRORS


def calculate_backoff(
    retry_count: int,
    base_delay: float,
    max_delay: float
) -> float:

    exponential_delay = base_delay * (2 ** retry_count)

    capped_delay = min(
        exponential_delay,
        max_delay
    )

    jitter = random.uniform(
        0,
        capped_delay * 0.2
    )

    return capped_delay + jitter