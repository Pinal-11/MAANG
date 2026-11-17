# Docker Multi-Stage Builds

## Learning objectives

-   Explain why build-time dependencies should not always ship in
    runtime images.
-   Create named stages with `FROM ... AS ...`.
-   Copy selected artifacts using `COPY --from`.
-   Understand final-stage behavior and `--target`.

## Why multi-stage builds?

Build environments may need compilers, development headers, build tools,
temporary source files, and development-only dependencies. The
application may not need these at runtime.

The goal: **Build everything you need, but ship only what you need to
run.**

Multi-stage builds separate build and runtime concerns. They do not
automatically make every image smaller; the final image is leaner only
when unnecessary files and dependencies are left out.

## Core syntax

``` dockerfile
FROM some-base-image AS builder
# Build or install artifacts

FROM some-runtime-image AS runtime
COPY --from=builder /path/to/artifact /destination/
```

Each `FROM` starts a new stage. A stage can be named with `AS`.
`COPY --from` copies selected files from another stage. By default, the
final stage is the resulting image. Earlier stages are not automatically
included.

## Python Notes API example

Assumptions: the build context is `app/`, the app file is `app.py`, and
`requirements.txt` contains Flask and `psycopg2-binary`.

``` dockerfile
# Stage 1: prepare dependencies
FROM python:3.12-slim AS builder

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: runtime
FROM python:3.12-slim AS runtime

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

What happens: 1. The builder creates a virtual environment. 2.
Dependencies are installed into `/opt/venv`. 3. The runtime stage starts
from a fresh Python base. 4. The virtual environment is copied from the
builder. 5. The app file is copied into the runtime image.

Both stages use the same Python base to help maintain compatibility.

**Limitation of this example:** The existing Notes API uses
`psycopg2-binary`, so this demonstrates stage separation and artifact
copying; it does not demonstrate a large reduction from removing a
compiler toolchain. In projects that compile native dependencies,
compilers and development headers can stay in the builder stage, while
the runtime stage contains only required runtime libraries and compiled
artifacts. Those runtime libraries must still be present.

## Build and verify

From the project root:

``` bash
docker compose build api
docker compose up -d
docker compose ps
docker compose logs api
curl http://localhost:8080/health
docker images
docker history YOUR_API_IMAGE
```

Expected health response:

``` json
{"status":"healthy"}
```

Do not remove the PostgreSQL volume as part of this exercise.

## Build a particular stage

``` bash
docker build --target builder -t notes-api-builder ./app
```

This is useful for debugging or producing a build/development image.
Without `--target`, Docker builds the final stage by default.

## Interview traps

-   **Does runtime inherit all builder files?** No. Each `FROM` starts a
    new stage; copy required artifacts explicitly.
-   **Does every `FROM` create a final image?** No. The final stage is
    the default output; `--target` can select another stage.
-   **Does multi-stage always reduce image size?** No. It helps when the
    final stage excludes unnecessary tools and files.
-   **Why use compatible builder and runtime environments?** Native
    artifacts may depend on OS, architecture, runtime, or ABI
    compatibility.

## Key takeaways

-   Name stages to separate build and runtime work.
-   Use `COPY --from` to select artifacts.
-   The final stage is the default output.
-   Keep unnecessary build tools out of the final stage.
-   Check compatibility when copying native artifacts.
-   Measure the result rather than assuming it is smaller.
