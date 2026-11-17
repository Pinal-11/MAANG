# Docker Fundamentals --- MAANG Interview Preparation Notes

> **Scope:** Docker images, containers, Dockerfile
> basics, build cache, writable layers, lifecycle, port publishing, and
> troubleshooting.

## 1. Why Docker?

Docker packages an application with its runtime, dependencies, and
required files so it can run consistently across environments. It helps
solve the "works on my machine" problem.

-   **Virtual machine:** Runs a guest operating system on virtualized
    hardware.
-   **Container:** Runs an isolated application process while sharing
    the host OS kernel.

Containers are generally lighter than full VMs because each container
does not need its own guest OS.

## 2. Docker image vs. container

**Image:** An immutable template containing application files, runtime,
dependencies, filesystem content, and image configuration.

**Container:** A running or stopped instance created from an image. It
has its own runtime state and writable container layer.

  -----------------------------------------------------------------------
  Image                               Container
  ----------------------------------- -----------------------------------
  Template used to create containers  Instance created from an image

  Read-only image layers              Adds a writable layer

  Can create many containers          Has its own lifecycle

  Can be stored locally or in a       Can be started, stopped, and
  registry                            removed
  -----------------------------------------------------------------------

Create multiple containers from one image:

``` bash
docker run -d --name app-1 my-app:v1
docker run -d --name app-2 my-app:v1
docker run -d --name app-3 my-app:v1
```

Containers can share the image's read-only layers, while each gets its
own writable layer and runtime state. Some resources can intentionally
be shared, such as volumes and network namespaces.

**When a container is removed:** Its writable layer is deleted. The
image remains unless separately removed. Data in separately managed
volumes or bind mounts can persist.

## 3. Essential Docker commands

### Images

``` bash
docker pull python:3.12-slim
docker images
docker build -t my-python-app:v1 .
docker rmi my-python-app:v1
```

### Containers

``` bash
docker run -d --name my-app my-python-app:v1
docker ps
docker ps -a
docker stop my-app
docker start my-app
docker rm my-app
docker logs my-app
docker logs -f my-app
docker logs --tail 100 my-app
docker exec -it my-app sh
docker exec -it my-app bash
```

`docker ps` lists running containers; `docker ps -a` includes stopped
containers. `docker exec` requires a running container. Bash may not be
installed in minimal images, so try `sh`.

## 4. Dockerfile fundamentals

A Dockerfile contains instructions used to build an image.

Example `app.py`:

``` python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello MAANG! Docker is working."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

Example `requirements.txt`:

``` text
Flask==3.1.0
```

Example `Dockerfile`:

``` dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

  Instruction   Purpose
  ------------- --------------------------------------------------------
  `FROM`        Selects the base image
  `WORKDIR`     Sets the working directory for subsequent instructions
  `COPY`        Copies files from the build context into the image
  `RUN`         Executes a command during image build
  `EXPOSE`      Documents the intended container port
  `CMD`         Sets the default command when a container starts

### RUN vs. CMD

-   `RUN` executes during image build; its filesystem changes are
    included in the image.
-   `CMD` defines the default command at container startup and can be
    overridden by arguments to `docker run`.
-   `ENTRYPOINT` configures the main executable for the container. `CMD`
    is often used to provide default arguments or a default command.

## 5. Build and run the example

From the directory containing the Dockerfile and application files:

``` bash
docker build -t my-python-app:v1 .
docker run -d --name my-python-app -p 5000:5000 my-python-app:v1
docker ps
curl http://localhost:5000
docker logs my-python-app
docker stop my-python-app
docker rm my-python-app
```

Removing the container does not automatically remove the image.

## 6. Docker layers and build cache

Docker can reuse cached results from earlier build steps when their
inputs have not changed.

Consider:

``` dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
```

Why copy `requirements.txt` first?

1.  Dependency manifests often change less frequently than application
    source code.
2.  If only `app.py` changes, Docker can reuse the cached
    dependency-installation step, assuming the relevant cache is
    available.
3.  Docker rebuilds the application-copy step and subsequent affected
    steps.
4.  If `requirements.txt` changes, the dependency-installation step must
    be rebuilt.

**Interview takeaway:** Copy relatively stable dependency files before
frequently changing source files to improve cache reuse.

Not every Dockerfile instruction creates a filesystem layer. For
example, `CMD` primarily contributes image configuration metadata.

### `.dockerignore`

Exclude unnecessary files from the build context:

``` text
__pycache__/
.git/
.venv/
.env
*.pyc
```

This reduces unnecessary build-context content. Avoid including secrets
in the build context.

## 7. Writable layer and persistent storage

A container adds a writable layer on top of the image's read-only
layers. Data written only to that layer is ephemeral.

  Storage                    Survives container removal?
  -------------------------- -----------------------------
  Container writable layer   No
  Named Docker volume        Yes, normally
  Bind mount                 Host-side files remain

**Interview answer:** Container writable-layer data is ephemeral. Use
persistent storage such as Docker volumes or bind mounts when data must
survive container recreation.

A volume has a lifecycle separate from the container. Removing a
container does not normally remove a named volume.

## 8. Container lifecycle and failure isolation

If three containers are created from the same image and one crashes, the
other two do not automatically stop merely because the first one
crashed. Each container has its own runtime lifecycle, and the image
remains available.

**Nuance:** Isolation does not remove shared dependencies. If all three
applications depend on the same database and that database fails, all
three may be affected.

## 9. Docker port publishing

Example:

``` bash
docker run -d --name payment-service -p 8080:5000 payment-app:v1
```

The syntax is:

``` text
-p HOST_PORT:CONTAINER_PORT
```

-   `8080` is the host port.
-   `5000` is the container port where the application should listen.
-   Docker publishes host port `8080` and forwards traffic to container
    port `5000`.

A request to `http://localhost:8080` on the host is forwarded to port
`5000` in the container.

### EXPOSE vs. -p

-   `EXPOSE 5000` documents the intended container port. It does not, by
    itself, publish the port to the host.
-   `-p 8080:5000` publishes a host port and maps it to a container
    port.

## 10. `127.0.0.1` vs. `0.0.0.0`

This is a critical container-networking concept.

### `127.0.0.1`

-   The loopback address.
-   Refers to the local machine or network namespace.
-   Inside a container, it refers to that container's own loopback
    interface.
-   An application bound only to `127.0.0.1` will not accept connections
    arriving through the container's other network interfaces.

### `0.0.0.0`

-   The IPv4 wildcard bind address.
-   Tells the application to listen on all available IPv4 interfaces.
-   It is a bind/listening address, not a bandwidth setting.
-   Clients normally connect to a reachable IP address or hostname, not
    to `0.0.0.0`.

### Flask example

Problematic for normal Docker port publishing:

``` python
app.run(host="127.0.0.1", port=5000)
```

Expected configuration:

``` python
app.run(host="0.0.0.0", port=5000)
```

**Why can localhost binding break Docker port publishing?**

Suppose the application listens on `127.0.0.1:5000` inside the
container, while Docker publishes host port `8080` to container port
`5000`. Docker forwards traffic through the container's network
interface, but the application is listening only on the container's
loopback interface. It therefore does not accept that forwarded
connection.

Binding to `0.0.0.0:5000` allows the application to listen on the
container's IPv4 interfaces, making it reachable through the published
port, subject to firewall and network configuration.

## 11. Production troubleshooting workflow

Scenario: The container appears to be running, but the application
cannot be reached.

### Step 1: Check container status

``` bash
docker ps
docker ps -a
```

### Step 2: Check application logs

``` bash
docker logs payment-service
docker logs -f payment-service
docker logs --tail 100 payment-service
```

Look for startup errors, exceptions, and port-binding problems.

### Step 3: Verify port mapping and configuration

``` bash
docker port payment-service
docker inspect payment-service
```

### Step 4: Enter the container

``` bash
docker exec -it payment-service sh
```

Or, if Bash is installed:

``` bash
docker exec -it payment-service bash
```

### Step 5: Test connectivity

From the host:

``` bash
curl http://localhost:8080
```

From inside the container, if `curl` is installed:

``` bash
curl http://127.0.0.1:5000
```

If the internal request works but the host request fails, investigate
port publishing, application binding, firewall rules, and Docker
networking.

### Troubleshooting checklist

  Check                     Command
  ------------------------- --------------------------------------
  Container status          `docker ps -a`
  Application logs          `docker logs payment-service`
  Port mapping              `docker port payment-service`
  Container configuration   `docker inspect payment-service`
  Shell access              `docker exec -it payment-service sh`
  Host connectivity         `curl http://localhost:8080`

## 12. Interview questions and model answers

### Q1. What is the difference between a Docker image and a container?

A Docker image is an immutable template containing the application,
runtime, dependencies, and filesystem content. A container is an
instance created from that image, with its own runtime state and
writable layer.

### Q2. Can multiple containers be created from one image?

Yes. They can share the image's read-only layers, while each container
has its own writable layer and runtime state.

### Q3. What is the difference between `RUN` and `CMD`?

`RUN` executes during image build. `CMD` defines the default command
when a container starts.

### Q4. Why copy `requirements.txt` before `app.py`?

It improves build-cache reuse. If application code changes but
dependencies do not, Docker can reuse the cached dependency-installation
step.

### Q5. What happens to the writable layer when a container is removed?

The container's writable layer is deleted. The image remains, and data
in separately managed persistent volumes or bind mounts can survive.

### Q6. If one container crashes, do other containers from the same image stop?

No. Containers have independent runtime lifecycles. A crash in one does
not automatically stop the others.

### Q7. What does `-p 8080:5000` mean?

It publishes host port `8080` and forwards traffic to container port
`5000`.

### Q8. Why should a containerized web application often bind to `0.0.0.0`?

It needs to listen on the container's network interfaces so traffic
forwarded by Docker can reach it. Binding only to `127.0.0.1` restricts
it to the container's loopback interface.

### Q9. Does `EXPOSE 5000` publish the port?

No. It documents the intended container port. Use `-p` with `docker run`
to publish a port to the host.

## 13. Key points to remember

1.  **Image = template; container = runtime instance.**
2.  **Image layers are read-only; a container adds a writable layer.**
3.  **Removing a container deletes its writable layer, not the image.**
4.  **Use volumes or bind mounts for data that must persist.**
5.  **`RUN` executes at build time; `CMD` defines a default runtime
    command.**
6.  **Copy dependency manifests before frequently changing source code
    to improve cache reuse.**
7.  **`EXPOSE` documents a port; `-p` publishes a port.**
8.  **`127.0.0.1` is loopback; `0.0.0.0` listens on all IPv4
    interfaces.**
9.  **A container crash does not automatically stop other independent
    containers.**
10. **Troubleshoot systematically: status → logs → port mapping →
    application binding → connectivity.**

## 14. Official documentation

-   [Docker: What is an
    image?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/)
-   [Docker: What is a
    container?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)
-   [Docker: Dockerfile
    reference](https://docs.docker.com/reference/dockerfile/)
-   [Docker: Build cache](https://docs.docker.com/build/cache/)
-   [Docker: Build best
    practices](https://docs.docker.com/build/building/best-practices/)

## 15. Suggested next topics

1.  Docker volumes and bind mounts.
2.  Multi-stage Docker builds.
3.  Docker image optimization and security.
4.  Docker networking: bridge, host, and custom networks.
5.  Docker Compose.
6.  Container health checks and restart policies.
7.  Production container troubleshooting.

**Study tip:** Do not just memorize commands. Practise explaining what
Docker is doing underneath---especially image layers, container
isolation, storage persistence, port forwarding, and application
binding.
