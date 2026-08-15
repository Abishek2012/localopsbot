# localopsbot

# LocalOpsBot

## Overview

LocalOpsBot is a lightweight operations chatbot platform designed with production-oriented DevOps and Kubernetes deployment practices.

The application includes:

- API service for handling requests
- Background worker for asynchronous processing
- Redis for task coordination
- Retry handling for failed processing
- Dead-letter handling for tasks that exceed retry limits
- Docker Compose for local execution
- Helm for Kubernetes deployment packaging

---

## Architecture

The application consists of the following components:

```text
                    +------------------+
                    |      Client      |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    API Service   |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |      Redis       |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Background Worker|
                    +------------------+



```

The API receives requests and submits work for asynchronous processing. Redis is used for coordination between the API service and the background worker.

Failed tasks are retried according to the configured retry policy. Tasks that exceed the retry limit are handled through the dead-letter workflow.

---

## Local Setup

### Prerequisites

Install:

- Docker Desktop
- Docker Compose
- Helm
- Git

### Clone the repository

```bash
git clone https://github.com/Abishek2012/localopsbot.git
cd localopsbot
```

### Start the application

```bash
docker compose up --build -d
```

### Check running containers

```bash
docker compose ps
```

### Stop the application

```bash
docker compose down
```

---

## Local Components

The Docker Compose environment includes:

- API container
- Background worker container
- Redis container

The API and worker communicate through Redis.




---

## Failure Handling

### Retry Handling

When processing fails, the application retries the task according to the configured retry policy.

The retry configuration includes:

- Maximum retry attempts
- Base retry delay
- Maximum retry delay

### Dead-Letter Handling

If a task continues to fail after reaching the configured retry limit, it is moved to the dead-letter workflow for further inspection.

This prevents permanently failing tasks from continuously blocking normal processing.

---

## Configuration

Application configuration is externalized through environment variables and Kubernetes configuration resources.

Examples include:

- Retry limits
- Retry delays
- Processing timeout
- Shutdown timeout
- Redis configuration

Sensitive configuration is separated from regular configuration when deployed to Kubernetes.


---

# Kubernetes Deployment

The application is packaged as a Helm chart for Kubernetes deployment.

The Helm deployment includes:

- API Deployment
- Worker Deployment
- Redis Deployment
- API Service
- Redis Service
- ConfigMap
- Secret
- HorizontalPodAutoscaler
- PodDisruptionBudget

## Resource Management

CPU and memory requests and limits are configured for the API, worker, and Redis workloads.

## Health Checks

The API deployment includes:

- Startup probe
- Liveness probe
- Readiness probe

These checks allow Kubernetes to determine whether the application has started successfully, is healthy, and is ready to receive traffic.

## Autoscaling

The API workload includes a Horizontal Pod Autoscaler.

The HPA defines:

- Minimum replicas
- Maximum replicas
- Target CPU utilization
- Scale-up behavior
- Scale-down stabilization

## Availability

A PodDisruptionBudget is included for the API workload to help maintain availability during voluntary disruptions.

## Security

The Kubernetes workloads include:

- Running containers as non-root
- Disabling privilege escalation
- Dropping Linux capabilities
- RuntimeDefault seccomp profile

Sensitive configuration is referenced through a Kubernetes Secret.

## Graceful Shutdown

The API and worker deployments define a termination grace period to allow in-flight processing to complete before containers are terminated.



---

# Helm Validation

The Helm chart was validated locally.

Run:

```bash
helm lint helm/localopsbot
```

Validation result:

```text
1 chart(s) linted, 0 chart(s) failed
```

The Kubernetes manifests were also rendered successfully using:

```bash
helm template localopsbot helm/localopsbot
```

The rendered output was checked to confirm the presence of:

- Secret
- HorizontalPodAutoscaler
- PodDisruptionBudget

## Deploying to a Kubernetes Cluster

In an environment with access to a Kubernetes cluster, deploy using:

```bash
helm install localopsbot helm/localopsbot
```

To upgrade an existing deployment:

```bash
helm upgrade localopsbot helm/localopsbot
```

To uninstall:

```bash
helm uninstall localopsbot
```




---

# Testing

Tests are available in the `tests/` directory.

Run the test suite with:

```bash
pytest
```

---

# Documentation

Additional project documentation is available in:

- `DESIGN.md` — architecture and design decisions
- `RUNBOOK.md` — operational and troubleshooting procedures

---

# Validation Approach and Known Limitation

The application was validated locally using Docker Compose.

The Kubernetes Helm chart was validated using:

```bash
helm lint helm/localopsbot
helm template localopsbot helm/localopsbot
```

A full local Kubernetes cluster was not used for the final validation workflow. The Helm chart and Kubernetes resources were validated through Helm linting and manifest rendering.

This validation approach verifies Helm syntax, template correctness, and the generated Kubernetes resources without requiring a local Kubernetes runtime.




## Kubernetes Validation

The Kubernetes deployment configuration was implemented using Helm and includes the application workloads, services, ConfigMap, Secret, health probes, resource configuration, HPA, and PodDisruptionBudget.

The Helm chart was validated using:

```bash
helm lint helm/localopsbot
helm template localopsbot helm/localopsbot
```

End-to-end validation against a running Kubernetes cluster was also attempted locally. Docker Desktop Kubernetes caused resource constraints on the development machine, so a lightweight `kind` cluster was attempted as an alternative. The `kind` control plane failed during bootstrap, after which the temporary cluster was cleaned up.

Therefore, the submitted Kubernetes configuration has been validated through Helm linting and manifest rendering, but full runtime validation on a running Kubernetes cluster was not completed in the local environment.
