# LocalOpsBot Runbook

## Purpose

This runbook provides operational procedures for identifying, troubleshooting, mitigating, and recovering from common LocalOpsBot failure scenarios.

The primary components are:

- API service
- Background worker
- Redis
- Retry mechanism
- Dead-letter workflow

---

# 1. Queue Backlog

## Symptoms

- Requests remain pending for an extended period.
- Redis queue length continues to increase.
- Background processing latency increases.

## Checks

Check running services:

```bash
docker compose ps
```

Check worker logs:

```bash
docker compose logs worker
```

Check Redis connectivity and application logs for queue-related errors.

## Mitigation

- Confirm the worker container is running.
- Restart the worker if it is unhealthy.
- Increase worker capacity if the backlog is caused by insufficient processing throughput.

```bash
docker compose restart worker
```

## Recovery

Monitor the queue and worker logs until queued tasks are processed successfully.

## Corrective Action

Investigate the cause of sustained backlog and adjust worker concurrency, processing capacity, or retry behavior where necessary.

---

# 2. LLM Timeout or Throttling

## Symptoms

- Requests fail after an upstream timeout.
- Processing latency increases.
- Retry attempts increase.
- Timeout or throttling errors appear in application logs.

## Checks

Check API and worker logs:

```bash
docker compose logs api
docker compose logs worker
```

Review timeout and retry-related configuration.

## Mitigation

The retry mechanism should retry transient failures using the configured backoff policy.

If the upstream service remains unavailable, prevent continuous immediate retries by allowing the configured retry delay to take effect.

## Recovery

Once the upstream dependency recovers, retry processing through the normal retry workflow.

## Corrective Action

Review timeout values, retry limits, and backoff configuration. Reduce dependency load or introduce additional capacity where appropriate.

---

# 3. Retrieval Failure

## Symptoms

- The chatbot cannot retrieve expected local knowledge.
- Requests return incomplete or fallback responses.
- Retrieval errors appear in logs.

## Checks

Check application logs:

```bash
docker compose logs api
```

Verify that the local knowledge base and retrieval configuration are available.

## Mitigation

Restore access to the local knowledge source and verify configuration.

## Recovery

Restart the affected service if necessary:

```bash
docker compose restart api
```

## Corrective Action

Validate retrieval configuration during deployment and add tests for unavailable or malformed knowledge sources.

---

# 4. Worker Crash Loop

## Symptoms

- The worker container repeatedly stops or restarts.
- Background jobs are not being processed.
- Queue backlog increases.

## Checks

Check container status:

```bash
docker compose ps
```

Check worker logs:

```bash
docker compose logs worker
```

## Mitigation

Identify the application or dependency error causing the crash.

Restart the worker after correcting the issue:

```bash
docker compose restart worker
```

## Recovery

Confirm that the worker remains healthy and queued tasks resume processing.

## Corrective Action

Add or improve validation, error handling, dependency health checks, and automated tests for the failure condition.

---

# 5. Duplicate Action Delivery

## Symptoms

- The same action appears to execute more than once.
- Duplicate requests or repeated side effects are observed.

## Checks

Review application and worker logs for duplicate task or action identifiers.

Verify that idempotency handling is functioning as expected.

## Mitigation

Use the action or request identifier to prevent duplicate processing.

Do not repeat the external side effect if the action has already been completed successfully.

## Recovery

Identify duplicate records and verify that only one successful action is retained.

## Corrective Action

Ensure idempotency keys are persisted and checked before executing actions.

---

# 6. Dead-Letter Queue Handling and Replay

## Symptoms

- A task exceeds the configured retry limit.
- The task is moved to the dead-letter workflow.
- Repeated processing failures are visible in logs.

## Checks

Identify the failed task and determine the root cause before replaying it.

Review worker logs:

```bash
docker compose logs worker
```

## Mitigation

Correct the underlying failure before replaying the task.

Do not continuously replay a task without resolving the cause of failure.

## Recovery

Replay the task through the supported dead-letter recovery workflow after the root cause has been corrected.

## Corrective Action

Review retry limits and error classification to ensure permanently failing tasks are not repeatedly retried.

---

# 7. Failed Deployment

## Symptoms

- A new deployment does not start successfully.
- Containers fail health checks.
- Kubernetes resources fail validation or rendering.

## Checks

For local containers:

```bash
docker compose ps
docker compose logs
```

For Helm validation:

```bash
helm lint helm/localopsbot
helm template localopsbot helm/localopsbot
```

## Mitigation

Identify the failing configuration or application change.

For a previously working Git version, revert the failing change:

```bash
git log --oneline
git revert <commit-id>
git push origin main
```

## Recovery

Re-run validation after the rollback or correction.

## Corrective Action

Validate Docker and Helm changes before deployment and require review for production configuration changes.

---

# 8. High Retry Rate

## Symptoms

- Retry activity increases significantly.
- Processing latency increases.
- More tasks approach the maximum retry limit.

## Checks

Review API and worker logs:

```bash
docker compose logs api
docker compose logs worker
```

Identify whether failures originate from:

- Redis
- Retrieval
- External dependencies
- Application processing

## Mitigation

Address the underlying dependency or application failure.

Allow the configured backoff policy to reduce repeated immediate retry attempts.

## Recovery

Monitor processing until the retry rate returns to normal and tasks complete successfully.

## Corrective Action

Review retry configuration, dependency health, timeout settings, and error classification.

---

# 9. Graceful Shutdown

## Procedure

Before stopping the application, allow in-flight work to complete where possible.

Stop the environment using:

```bash
docker compose down
```

For a restart:

```bash
docker compose up -d
```

Verify service status:

```bash
docker compose ps
```

Review worker logs to confirm that processing resumes correctly.

---

# Operational Validation

Useful validation commands:

```bash
docker compose ps
docker compose logs api
docker compose logs worker
helm lint helm/localopsbot
helm template localopsbot helm/localopsbot
pytest
```