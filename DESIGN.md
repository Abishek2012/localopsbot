# LocalOpsBot Design

## Architecture Overview

LocalOpsBot is designed as a lightweight asynchronous operations platform.

The system consists of three main components:

- API Service
- Background Worker
- Redis

The API receives incoming requests and submits asynchronous work through Redis. The background worker processes queued tasks independently.

This asynchronous design separates request handling from background processing and allows failed work to be retried without blocking the API.

---

## Request Flow

```text
Client
   |
   v
API Service
   |
   v
Redis Queue
   |
   v
Background Worker
   |
   +----------------------+
   |                      |
   v                      v
Success              Processing Failure
                          |
                          v
                    Retry Decision
                          |
              +-----------+-----------+
              |                       |
              v                       v
         Retryable Error         Non-Retryable Error
              |
              v
      Exponential Backoff
          with Jitter
              |
              v
         Redis Queue
              |
              v
      Retry Limit Reached
              |
              v
        Dead-Letter Queue


## Component Responsibilities

### API Service

The API service receives client requests and performs request validation.

Accepted requests are submitted for asynchronous processing rather than being processed synchronously. This keeps the API responsive when downstream processing is slow or temporarily unavailable.

The API also exposes health and readiness endpoints for operational monitoring and Kubernetes probes.

### Redis

Redis is used as the coordination layer between the API service and the background worker.

It provides the queue used to submit and retrieve asynchronous tasks.

Redis also supports retry and dead-letter handling for failed tasks.

### Background Worker

The background worker continuously retrieves queued tasks and processes them independently from the API.

The worker is responsible for:

- Processing asynchronous tasks
- Classifying failures
- Retrying retryable failures
- Applying exponential backoff with jitter
- Enforcing retry limits
- Enforcing processing time limits
- Moving exhausted tasks to dead-letter handling
- Updating operational metrics
- Supporting graceful shutdown


---

## Failure Handling

Failures are classified to determine whether they should be retried.

Retryable failures include temporary conditions such as:

- Timeout
- Rate limiting
- Server errors
- Malformed responses
- Retrieval failures

Retryable tasks use exponential backoff with jitter before being processed again.

The retry delay increases with each retry attempt and is capped at a configured maximum delay.

A maximum retry limit prevents tasks from being retried indefinitely.

Tasks that exceed the configured retry limit are moved to the dead-letter workflow for investigation.

Non-retryable failures are not repeatedly retried.

---

## Timeout Handling

The worker enforces a maximum processing time for tasks.

If processing exceeds the configured time limit, the task is treated as a failure and handled through the configured retry or failure workflow.

This prevents a single task from consuming worker capacity indefinitely.

---

## Duplicate Processing Considerations

Distributed task processing can result in duplicate delivery.

The application uses task identifiers and duplicate-handling logic to reduce the risk of repeated processing and repeated side effects.

For production environments, idempotency keys or persistent task identifiers should ensure repeated delivery does not result in repeated external side effects.

---

## Observability

The application provides operational visibility through metrics and structured logging.

Metrics include:

- Jobs processed
- Processing failures
- Retry attempts
- Dead-lettered jobs
- Processing duration
- Queue depth

Application logs include identifiers and failure information to support troubleshooting and operational investigation.

---

## Deployment Design

### Docker Compose

Docker Compose provides a lightweight local environment containing:

- API service
- Background worker
- Redis

### Kubernetes

The application is packaged as a Helm chart for Kubernetes deployment.

The Kubernetes configuration includes:

- API Deployment
- Worker Deployment
- Redis Deployment
- Services
- ConfigMap
- Secret
- Resource requests and limits
- Startup probe
- Liveness probe
- Readiness probe
- Horizontal Pod Autoscaler
- PodDisruptionBudget
- Security context configuration
- Graceful termination settings

Helm templates are parameterized through `values.yaml`.



---

## Security Design

The Kubernetes workloads are configured with production-oriented security settings.

These include:

- Running containers as non-root
- Disabling privilege escalation
- Dropping Linux capabilities
- Using the RuntimeDefault seccomp profile
- Separating sensitive configuration into Kubernetes Secrets

Application secrets are referenced by the deployment rather than being hardcoded directly into container configuration.

---

## GitOps Design

An Argo CD Application manifest is included under:

`deploy/gitops/application.yaml`

The GitOps configuration points Argo CD to the Helm chart in this repository:

`helm/localopsbot`

The desired application state is therefore defined declaratively in Git. Argo CD can synchronize the cluster state with the repository configuration and detect configuration drift.

The configuration uses automated synchronization with:

- Pruning of resources that are no longer defined
- Self-healing when cluster resources drift from the desired state
- Automatic namespace creation

This provides a GitOps-oriented deployment model where infrastructure and application deployment configuration can be reviewed and tracked through Git history.

---

## Operational Considerations

Operational procedures and common failure scenarios are documented separately in `RUNBOOK.md`.

The runbook covers:

- Queue backlog
- LLM timeout or throttling
- Retrieval failures
- Worker crash loops
- Duplicate action delivery
- Dead-letter queue handling and replay
- Failed deployments
- High retry rates
- Graceful shutdown

Each scenario includes symptoms, checks, mitigation, recovery, and corrective actions where applicable.

This separates the system architecture and design decisions from day-to-day operational troubleshooting.