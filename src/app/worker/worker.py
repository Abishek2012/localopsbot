import signal
import time
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import (
    create_job,
    initialize_database,
    move_to_dead_letter,
    update_job_status
)
from app.core.logging import logger
from app.core.metrics import (
    DLQ_JOBS_TOTAL,
    JOB_RETRIES_TOTAL,
    JOBS_TOTAL,
    PROCESSING_DURATION,
    QUEUE_DEPTH
)
from app.core.retry import (
    calculate_backoff,
    is_retryable
)
from app.services.mock_llm import (
    LLMError,
    mock_llm_service
)
from app.services.queue import queue_service
from app.services.retrieval import (
    RetrievalError,
    retrieval_service
)


running = True
current_job = None


def handle_shutdown(signum, frame):
    global running

    logger.info(
        "Shutdown signal received. Stopping worker."
    )

    running = False


def process_job(job: dict):
    start_time = time.monotonic()

    retry_count = 0
    retry_history = []

    job_id = job["job_id"]

    logger.info(
        "Processing job",
        extra={
            "job_id": job_id,
            "conversation_id": job["conversation_id"],
            "retry_count": retry_count
        }
    )

    create_job(job)

    while retry_count <= settings.max_retries:

        attempt_start = time.monotonic()

        try:
            update_job_status(
                job_id,
                status="processing",
                retry_count=retry_count,
                retry_history=retry_history
            )

            elapsed = (
                time.monotonic()
                - start_time
            )

            if elapsed > settings.max_processing_time_seconds:
                raise LLMError(
                    "Maximum processing time exceeded",
                    "timeout"
                )

            context = retrieval_service.retrieve(
                job["message"]
            )

            result = mock_llm_service.generate(
                job["message"],
                context
            )

            duration = (
                time.monotonic()
                - start_time
            )

            update_job_status(
                job_id,
                status="completed",
                retry_count=retry_count,
                retry_history=retry_history,
                response=result["response"]
            )

            JOBS_TOTAL.labels(
                status="completed"
            ).inc()

            PROCESSING_DURATION.observe(
                duration
            )

            logger.info(
                "Job completed",
                extra={
                    "job_id": job_id,
                    "conversation_id": (
                        job["conversation_id"]
                    ),
                    "retry_count": retry_count,
                    "processing_duration": duration
                }
            )

            return

        except (LLMError, RetrievalError) as exc:

            error_category = getattr(
                exc,
                "category",
                "unknown"
            )

            retry_history.append({
                "attempt": retry_count + 1,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "error_category": error_category,
                "error": str(exc),
                "duration": (
                    time.monotonic()
                    - attempt_start
                )
            })

            retryable = is_retryable(
                error_category
            )

            if (
                not retryable
                or retry_count >= settings.max_retries
            ):
                update_job_status(
                    job_id,
                    status="dead_lettered",
                    retry_count=retry_count,
                    failure_reason=str(exc),
                    retry_history=retry_history
                )

                move_to_dead_letter(
                    job,
                    str(exc),
                    retry_history
                )

                JOBS_TOTAL.labels(
                    status="failed"
                ).inc()

                DLQ_JOBS_TOTAL.inc()

                logger.error(
                    "Job moved to dead letter store",
                    extra={
                        "job_id": job_id,
                        "conversation_id": (
                            job["conversation_id"]
                        ),
                        "retry_count": retry_count,
                        "error_category": (
                            error_category
                        )
                    }
                )

                return

            delay = calculate_backoff(
                retry_count,
                settings.retry_base_delay,
                settings.retry_max_delay
            )

            JOB_RETRIES_TOTAL.labels(
                dependency=(
                    "llm"
                    if isinstance(exc, LLMError)
                    else "retrieval"
                ),
                error_category=error_category
            ).inc()

            JOBS_TOTAL.labels(
                status="retried"
            ).inc()

            logger.warning(
                "Retrying job",
                extra={
                    "job_id": job_id,
                    "conversation_id": (
                        job["conversation_id"]
                    ),
                    "retry_count": retry_count,
                    "error_category": (
                        error_category
                    )
                }
            )

            retry_count += 1

            time.sleep(delay)

        except Exception as exc:

            retry_history.append({
                "attempt": retry_count + 1,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "error_category": "unexpected_error",
                "error": str(exc)
            })

            update_job_status(
                job_id,
                status="dead_lettered",
                retry_count=retry_count,
                failure_reason=str(exc),
                retry_history=retry_history
            )

            move_to_dead_letter(
                job,
                str(exc),
                retry_history
            )

            JOBS_TOTAL.labels(
                status="failed"
            ).inc()

            DLQ_JOBS_TOTAL.inc()

            logger.exception(
                "Unexpected job failure",
                extra={
                    "job_id": job_id
                }
            )

            return


def run_worker():
    global current_job

    signal.signal(
        signal.SIGTERM,
        handle_shutdown
    )

    signal.signal(
        signal.SIGINT,
        handle_shutdown
    )

    initialize_database()

    queue_service.connect()

    logger.info(
        "Worker started"
    )

    shutdown_start = None

    while running:

        try:
            QUEUE_DEPTH.set(
                queue_service.get_depth()
            )

            job = queue_service.dequeue(
                timeout=1
            )

            if job is None:
                continue

            current_job = job

            process_job(job)

            current_job = None

        except Exception:

            logger.exception(
                "Worker loop error"
            )

            time.sleep(1)

    logger.info(
        "Worker stopped accepting new jobs"
    )

    if current_job is not None:

        shutdown_start = time.monotonic()

        while (
            current_job is not None
            and (
                time.monotonic()
                - shutdown_start
                < settings.shutdown_timeout_seconds
            )
        ):
            time.sleep(0.1)

    logger.info(
        "Worker shutdown complete"
    )


if __name__ == "__main__":
    run_worker()