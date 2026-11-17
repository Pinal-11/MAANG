# Day 3 --- Block 3: Docker Notes

These notes are split by topic for focused revision.

## Topic index

1.  [Docker Image Layering and Build
    Cache](03-docker-image-layering-and-cache.md)
    -   Images vs. containers
    -   Read-only image layers and writable container layer
    -   Volumes and bind mounts
    -   Build cache and Dockerfile ordering
2.  [Docker Multi-Stage Builds](04-docker-multi-stage-builds.md)
    -   Builder and runtime stages
    -   `FROM ... AS ...`
    -   `COPY --from`
    -   Final-stage behavior and Python example
3.  [Docker Build Context and
    `.dockerignore`](05-dockerignore-and-build-context.md)
    -   Build context
    -   `.dockerignore` location and patterns
    -   Rule ordering and negation
    -   Build-context hygiene and secrets
4.  [Production Docker Best
    Practices](06-production-docker-best-practices.md)
    -   Non-root containers
    -   Image optimization and security
    -   Health checks
    -   Graceful shutdown
    -   Network exposure and secrets

## Suggested revision order

Read the topics in order. Then practice the commands and answer the
interview questions at the end of each note without looking at the
explanations.

## Project context

The examples use the Flask + PostgreSQL Notes API discussed in the
learning session. The Compose build context for the API is `./app`, and
the API is published on host port `8080` to container port `5000`.

Keep your PostgreSQL named volume intact when rebuilding or changing the
API image.
