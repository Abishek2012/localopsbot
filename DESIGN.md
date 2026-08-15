# LocalOpsBot Design

## Architecture Overview

LocalOpsBot is designed as a lightweight asynchronous operations platform.

The system consists of three main components:

- API Service
- Background Worker
- Redis

The API receives incoming requests and submits asynchronous work through Redis. The background worker processes the queued tasks independently.

## Request Flow

```text
Client
   |
   v
API Service
   |
   v
Redis
   |
   v
Background Worker