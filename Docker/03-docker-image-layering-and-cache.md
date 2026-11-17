# Docker Image Layering and Build Cache

## Learning objectives

-   Distinguish images, containers, image layers, and writable layers.
-   Understand persistence and Docker build caching.
-   Explain why Dockerfile instruction order matters.

## Image vs. container

-   **Image:** read-only template used to create containers.
-   **Container:** an instance of an image, with runtime configuration
    and a container-specific writable layer.

Multiple containers created from the same image can share its read-only
image layers. Each container has its own writable layer.

  -----------------------------------------------------------------------
  Storage                 What it stores          Lifecycle
  ----------------------- ----------------------- -----------------------
  Image layers            Read-only image         Remain while
                          filesystem content      image/layers are
                                                  retained

  Container writable      Changes made inside a   Removed with the
  layer                   container               container

  Named volume            Persistent application  Independent of
                          data managed by Docker  container lifecycle

  Bind mount              A host path mounted     Data remains at the
                          into a container        host path
  -----------------------------------------------------------------------

Do not store important persistent data only in a container's writable
layer. Use a volume or bind mount.

## Image layers

A useful mental model is that an image is assembled from filesystem
changes and image configuration. Instructions such as `RUN`, `COPY`, and
`ADD` commonly create filesystem layers in the classic builder model.
Instructions such as `CMD`, `ENTRYPOINT`, `ENV`, and `EXPOSE` primarily
configure image metadata. `WORKDIR` may create the directory if it does
not exist.

**Nuance:** BuildKit and modern Docker internals are more sophisticated
than the simplified rule "one Dockerfile instruction equals one layer."
Use this as a conceptual model, not a complete description of every
internal detail.

## Container filesystem

At runtime, the container sees a merged filesystem view: read-only image
layers plus its own writable layer. Copy-on-write behavior may copy a
file into the writable layer before a modification is made.

-   Changes in one container's writable layer do not modify the image.
-   Another container using the same image does not see those
    writable-layer changes.
-   Removing the container removes its writable layer.
-   Mounted volumes and bind mounts are separate from that layer.

## Build cache

Docker can reuse earlier build results when the relevant instructions
and inputs have not changed.

Cache-friendly Dockerfile:

``` dockerfile
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
CMD ["python", "app.py"]
```

If only `app.py` changes, Docker can often reuse the
dependency-installation step. If `requirements.txt` changes, that step
must be rebuilt.

Less cache-friendly pattern:

``` dockerfile
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

A change to any file included by the broad copy can invalidate that step
and later dependent steps. Copy infrequently changing dependency
manifests before frequently changing application code.

## Useful commands

``` bash
docker images
docker history YOUR_IMAGE
docker history --no-trunc YOUR_IMAGE
docker compose build api
docker compose build --no-cache api
docker inspect CONTAINER_NAME --format '{{json .Mounts}}'
```

To observe caching: build once, make a harmless comment-only change in
`app.py`, rebuild, then change `requirements.txt` and rebuild again.

## Interview questions

**What is the difference between an image and a container?** An image is
a read-only template; a container is an instance with a separate
writable layer and runtime configuration.

**Do two containers using the same image duplicate all image layers?**
They can share the read-only image layers, while each has its own
writable layer.

**Does deleting a container delete its image?** No. Their lifecycles are
separate.

**Why copy `requirements.txt` before application code?** To reuse
dependency-installation cache when only application source changes.

**Are volumes part of the writable layer?** No. They are separate mounts
and can outlive a container.

## Key takeaways

-   Image layers are reusable read-only image content.
-   Containers add their own writable layer.
-   Writable-layer data is ephemeral.
-   Use volumes or bind mounts for persistent data.
-   Docker cache depends on instructions and their inputs.
-   Order Dockerfile instructions to avoid unnecessary cache
    invalidation.
