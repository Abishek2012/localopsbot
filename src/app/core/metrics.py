from prometheus_client import Counter, Gauge, Histogram


CHAT_REQUESTS_TOTAL = Counter(
    "localopsbot_chat_requests_total",
    "Total chatbot requests",
    ["status"]
)

JOBS_TOTAL = Counter(
    "localopsbot_jobs_total",
    "Total background jobs",
    ["status"]
)

JOB_RETRIES_TOTAL = Counter(
    "localopsbot_job_retries_total",
    "Total job retries",
    ["dependency", "error_category"]
)

DLQ_JOBS_TOTAL = Counter(
    "localopsbot_dead_letter_jobs_total",
    "Total jobs moved to dead letter storage"
)

QUEUE_DEPTH = Gauge(
    "localopsbot_queue_depth",
    "Current queue depth"
)

PROCESSING_DURATION = Histogram(
    "localopsbot_processing_duration_seconds",
    "Job processing duration"
)

LLM_DURATION = Histogram(
    "localopsbot_llm_duration_seconds",
    "Mock LLM request duration"
)

LLM_ERRORS_TOTAL = Counter(
    "localopsbot_llm_errors_total",
    "Total LLM errors",
    ["error_category"]
)

RETRIEVAL_DURATION = Histogram(
    "localopsbot_retrieval_duration_seconds",
    "Retrieval request duration"
)

RETRIEVAL_ERRORS_TOTAL = Counter(
    "localopsbot_retrieval_errors_total",
    "Total retrieval errors",
    ["error_category"]
)

ACTION_EXECUTIONS_TOTAL = Counter(
    "localopsbot_action_executions_total",
    "Total action executions",
    ["status"]
)