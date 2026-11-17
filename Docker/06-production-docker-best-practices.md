# Production Docker Best Practices

## Learning objectives

-   Apply least privilege to containers.
-   Keep runtime images focused.
-   Understand health checks and graceful shutdown.
-   Limit network exposure.
-   Handle secrets safely.

## Run as a non-root user

Many images run as root unless configured otherwise. Running the
application as root can increase the impact of an application
compromise. Prefer a dedicated unprivileged user.

Example runtime stage:

``` dockerfile
FROM python:3.12-slim AS runtime

RUN groupadd --system app && \
    useradd --system --gid app --create-home app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app.py .

ENV PATH="/opt/venv/bin:$PATH"

USER app
EXPOSE 5000
CMD ["python", "app.py"]
```

Verify:

``` bash
docker compose exec api id
```

The UID should be non-zero, not `uid=0(root)`. Check file permissions:
the app must be able to read its files and write only where needed.

## Image optimization and attack-surface reduction

-   Use trusted, maintained base images.
-   Choose slim runtime images when appropriate.
-   Use multi-stage builds to exclude unnecessary build tools.
-   Pin dependency versions and update deliberately.
-   Avoid shipping unnecessary debugging and development packages.
-   Scan images for known vulnerabilities.
-   Rebuild regularly to incorporate maintained base-image and
    dependency updates.

Smaller does not automatically mean secure. Trust, patching,
configuration, and vulnerability management still matter.

## Linux capabilities and runtime restrictions

Drop capabilities the application does not need:

``` bash
docker run --cap-drop=ALL my-image
```

Add back only specific capabilities if there is a justified requirement.

Prevent privilege escalation:

``` bash
docker run --security-opt=no-new-privileges my-image
```

A read-only root filesystem can reduce writable locations:

``` bash
docker run --read-only my-image
```

If the application needs temporary writable storage, explicitly provide
it, for example with a tmpfs mount for `/tmp`. Test restrictions against
actual application requirements.

## Health checks: running is not healthy

A running container means its main process is running; it does not prove
that the application is ready to serve requests.

Example Dockerfile health check for the Notes API:

``` dockerfile
HEALTHCHECK --interval=30s \
            --timeout=3s \
            --start-period=5s \
            --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"
```

  Option             Meaning
  ------------------ ----------------------------------------------
  `--interval`       Time between checks
  `--timeout`        Maximum time allowed for a check
  `--start-period`   Startup grace period
  `--retries`        Consecutive failures before unhealthy status

Inspect:

``` bash
docker inspect --format='{{.State.Health.Status}}' CONTAINER_NAME
```

Possible states include `starting`, `healthy`, and `unhealthy`.

A health check reports status. It does not, by itself, automatically
restart an unhealthy container. An orchestrator or another recovery
mechanism may act on that status.

### Liveness vs. readiness

The example `/health` endpoint returns healthy without checking
PostgreSQL. That is closer to a basic application/liveness check. A
readiness check should verify that dependencies required to serve
requests are available. Design checks carefully to avoid unnecessary
restart loops.

## Graceful shutdown: SIGTERM and SIGKILL

When Docker stops a container, it normally: 1. Sends SIGTERM to the
container's main process. 2. Waits for the configured stop timeout. 3.
Sends SIGKILL if the process has not exited.

The application should stop accepting new work, finish or safely cancel
in-flight requests, close connections, release resources, and exit
before the timeout expires.

Prefer exec form:

``` dockerfile
CMD ["python", "app.py"]
```

Compared with shell form:

``` dockerfile
CMD python app.py
```

Exec form avoids a shell intermediary in the normal invocation and makes
signal delivery more straightforward.

For production Flask deployments, use a production WSGI server such as
Gunicorn rather than Flask's built-in development server. Configure
worker shutdown and request handling appropriately.

## Network exposure

Notes API architecture:

``` text
External client
      |
      | host port 8080
      v
API container:5000
      |
      | Docker network, service name db
      v
PostgreSQL container:5432
```

Compose example:

``` yaml
services:
  api:
    ports:
      - "127.0.0.1:8080:5000"

  db:
    # No host port mapping
```

The API reaches PostgreSQL over the shared Docker network using
`db:5432`. Inside the API container, `localhost` refers to the API
container itself, not the database.

If only containers on an internal network need PostgreSQL, there is
usually no need to publish its port to the host.

A mapping such as:

``` yaml
ports:
  - "8080:5000"
```

normally publishes on all host interfaces. For local-only access, bind
to loopback:

``` yaml
ports:
  - "127.0.0.1:8080:5000"
```

Use separate networks for services with different trust requirements.
Avoid exposing internal services publicly without a deliberate design.
Avoid mounting `/var/run/docker.sock` into ordinary application
containers; Docker daemon access is highly privileged.

## Secrets management

Avoid putting secrets directly in Dockerfiles:

``` dockerfile
ENV DB_PASSWORD=my-secret-password
```

Values baked into image configuration can be exposed through inspection
and distribution workflows.

Development: - Keep local environment variables in `.env` where
appropriate. - Exclude `.env` from the build context. - Do not commit
secrets to Git.

Production: - Use dedicated secret management. - Use BuildKit secret
mounts for build-time secrets. - Use the platform's runtime secret
mechanism for application credentials. - Rotate credentials and restrict
access.

`.dockerignore` is useful but is not a complete secret-management
solution.

## Production checklist

  Area            Practice
  --------------- -----------------------------------------------
  User            Run as non-root
  Base image      Use a trusted, maintained image
  Build           Use multi-stage builds where beneficial
  Build context   Exclude unnecessary files
  Dependencies    Pin, scan, and update dependencies
  Privileges      Drop unnecessary capabilities
  Filesystem      Use read-only root filesystem where practical
  Health          Configure meaningful health checks
  Shutdown        Handle SIGTERM gracefully
  Networking      Publish only required ports
  Secrets         Do not bake credentials into images
  Monitoring      Scan images and monitor runtime behavior

## Interview questions

**Why run a container as non-root?** It follows least privilege and
reduces the impact of a compromise.

**Does a running container mean the app is healthy?** No. Running
describes the main process state; a health check tests a configured
condition.

**Does Docker restart a container just because it becomes unhealthy?** A
health check reports status; recovery depends on an orchestrator or
other configured mechanism.

**What happens when Docker stops a container?** Docker normally sends
SIGTERM, waits for the stop timeout, then sends SIGKILL if needed.

**Why prefer exec-form CMD?** It avoids a shell intermediary and makes
signal delivery more straightforward.

**Why leave database ports unpublished?** If only containers on an
internal network need database access, publishing the port unnecessarily
expands network exposure.

**Is `.dockerignore` enough to protect secrets?** No. It is one
safeguard, not a replacement for secret management.

## Key takeaways

-   Apply least privilege.
-   Keep runtime images focused and maintained.
-   Distinguish liveness, readiness, and health.
-   Design graceful shutdown.
-   Expose only necessary ports.
-   Use dedicated secret-management practices.
