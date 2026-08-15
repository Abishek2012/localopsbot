import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "localopsbot",
            "message": record.getMessage(),
        }

        for field in [
            "request_id",
            "conversation_id",
            "job_id",
            "idempotency_key",
            "retry_count",
            "dependency",
            "error_category",
            "processing_duration"
        ]:
            value = getattr(record, field, None)

            if value is not None:
                log_data[field] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_data)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger()

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


logger = setup_logging()