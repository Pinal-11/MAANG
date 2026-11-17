# Docker Build Context and `.dockerignore`

## Learning objectives

-   Define Docker build context.
-   Explain `.dockerignore` and its correct location.
-   Understand matching and negation patterns.
-   Explain how it helps build hygiene and reduces accidental exposure.

## Build context

The build context is the set of files made available to the builder.

``` bash
docker build -t notes-api ./app
```

Here, `./app` is the build context. Dockerfile `COPY` and `ADD`
instructions can access files made available in that context; files
outside it are not normally available to those instructions.

Example:

``` text
app/
├── app.py
├── requirements.txt
├── Dockerfile
├── .env
├── __pycache__/
├── .venv/
└── tests/
```

Not all these files need to be sent to the builder or included in the
image.

## What is `.dockerignore`?

A `.dockerignore` file tells Docker which files and directories to
exclude from the build context.

  -----------------------------------------------------------------------
  `.gitignore`                        `.dockerignore`
  ----------------------------------- -----------------------------------
  Controls which files Git ignores    Controls which files are excluded
                                      from Docker build context

  Applies to Git tracking             Applies to Docker builds
  -----------------------------------------------------------------------

Benefits: - Avoid sending unnecessary files as part of the build
context. - Reduce build overhead. - Avoid accidentally copying local
files through broad `COPY` instructions. - Reduce the chance that local
secrets or development artifacts are exposed to the builder.

It is not a complete secrets-management system.

## Correct location

If Compose contains:

``` yaml
services:
  api:
    build: ./app
```

The build context is `app/`. Put `.dockerignore` inside `app/`:

``` text
docker-compose-lab/
├── app/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
└── compose.yaml
```

## Example `.dockerignore`

``` dockerignore
# Git files
.git
.gitignore

# Python cache
__pycache__/
*.py[cod]
*.pyo

# Virtual environments
.venv/
venv/

# Environment files and local secrets
.env
.env.*

# Tests and coverage
tests/
.coverage
.pytest_cache/

# Logs
*.log

# Editor settings
.vscode/
.idea/
```

Review patterns before adopting them. Do not exclude files that the
Dockerfile needs.

## Pattern matching and negation

  Pattern        Intended use
  -------------- ----------------------------------------------------
  `*.log`        Match log files at the relevant root pattern level
  `**/*.log`     Match log files at any directory depth
  `.env`         Exclude a root `.env` file
  `.venv/`       Exclude a virtual environment directory
  `!README.md`   Re-include `README.md` after a matching exclusion

Docker supports `**` to match any number of directories. Rules are
evaluated in order; the last matching rule determines whether a path is
included or excluded.

Example:

``` dockerignore
*.md
!README.md
```

This excludes Markdown files but re-includes `README.md`.

If a later rule excludes `README.md` again, it is excluded:

``` dockerignore
*.md
!README.md
README.md
```

## What if Dockerfile copies an ignored file?

If `.env` is excluded:

``` dockerignore
.env
```

but the Dockerfile contains:

``` dockerfile
COPY .env .
```

The build cannot copy the file from the context, so the build fails.

## `.dockerignore` vs. `COPY --exclude`

-   `.dockerignore` excludes paths from the overall build context.
-   `COPY --exclude` excludes matching paths from a particular `COPY`
    operation, where supported by the builder/version in use.

## Secrets

Do not rely only on `.dockerignore`: - Do not commit `.env` files
containing credentials. - Exclude local environment files from the build
context. - Do not bake passwords or tokens into Dockerfile `ARG` or
`ENV`. - Use BuildKit secret mounts for build-time secrets. - Use an
appropriate runtime secret-management mechanism in production.

## Hands-on verification

``` bash
docker compose build --no-cache api
docker compose up -d
docker compose ps
curl http://localhost:8080/health
```

Observe the build output, including the build-context loading step.
`.dockerignore` does not delete local files.

## Interview questions

**What is a Docker build context?** The set of files made available to
the builder for a build.

**Does `.dockerignore` delete files?** No. It excludes them from the
build context.

**Where should `.dockerignore` go?** At the root of the build context.

**Does it guarantee secret protection?** No. Use proper build-time and
runtime secret management.

**What if `COPY` references an ignored file?** The file is unavailable
in the context and the copy fails.

## Key takeaways

-   Understand the build context before writing ignore rules.
-   Put `.dockerignore` at the context root.
-   Exclude caches, local environments, logs, and secrets where
    appropriate.
-   Rule order matters.
-   It does not delete local files or replace secret management.
