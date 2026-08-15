import json
import time
from pathlib import Path

from app.core.metrics import (
    RETRIEVAL_DURATION,
    RETRIEVAL_ERRORS_TOTAL
)


class RetrievalError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.category = "retrieval_error"


class RetrievalService:

    def __init__(self):

        data_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "knowledge_base.json"
        )

        with open(
            data_path,
            "r",
            encoding="utf-8"
        ) as file:
            self.documents = json.load(file)

        self.failure_mode = "success"

    def set_failure_mode(
        self,
        mode: str
    ):

        if mode not in {
            "success",
            "retrieval_error"
        }:
            raise ValueError(
                f"Invalid retrieval mode: {mode}"
            )

        self.failure_mode = mode

    def retrieve(
        self,
        query: str,
        top_k: int = 2
    ) -> list[dict]:

        start_time = time.perf_counter()

        try:

            if (
                self.failure_mode
                == "retrieval_error"
            ):
                raise RetrievalError(
                    "Retrieval service unavailable"
                )

            query_words = set(
                query.lower().split()
            )

            scored_documents = []

            for document in self.documents:

                searchable_text = (
                    f"{document['title']} "
                    f"{document['content']}"
                ).lower()

                score = sum(
                    1
                    for word in query_words
                    if word in searchable_text
                )

                if score > 0:

                    scored_documents.append(
                        (score, document)
                    )

            scored_documents.sort(
                key=lambda item: item[0],
                reverse=True
            )

            results = [
                document
                for _, document
                in scored_documents[:top_k]
            ]

            RETRIEVAL_DURATION.observe(
                time.perf_counter()
                - start_time
            )

            return results

        except RetrievalError:

            RETRIEVAL_ERRORS_TOTAL.labels(
                error_category="retrieval_error"
            ).inc()

            raise

        except Exception as exc:

            RETRIEVAL_ERRORS_TOTAL.labels(
                error_category="retrieval_error"
            ).inc()

            raise RetrievalError(
                f"Retrieval failed: {str(exc)}"
            ) from exc


retrieval_service = RetrievalService()