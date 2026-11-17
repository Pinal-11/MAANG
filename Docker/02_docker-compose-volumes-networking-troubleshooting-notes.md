# Docker Volumes, Networking, Compose & Troubleshooting — Topic-wise Notes

**Focus:** Hands-on Notes API (Flask + PostgreSQL), Docker fundamentals, and DevOps interview troubleshooting.

## 1. Docker container storage and persistence

### Container writable layer
- An image provides the read-only starting filesystem; each container has its own writable layer.
- Files written only to that layer are removed when that container is removed.
- Restarting the **same** container does not, by itself, delete its writable layer; **removing/recreating** it does.

### Named Docker volumes
- A named volume is managed by Docker and exists independently of a particular container.
- Use it for data that must survive container replacement, such as PostgreSQL data.
- A volume can be attached to a new container. It is not automatically backed up.
- Never assume a named volume is the **correct** named volume just because one exists.

**Compose example:**

```yaml
services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

### Named volume vs bind mount

| Aspect | Named volume | Bind mount |
|---|---|---|
| Source | Docker-managed storage | Specific host path |
| Typical use | Database persistence, shared container data | Local development and source-code mounts |
| Lifecycle | Independent of a container | Host file/directory remains independently |
| Important caution | Back up and verify correct attachment | Host path and permissions matter |

## 2. Docker Compose lifecycle and volumes

```bash
docker compose up -d --build    # Build/start services
docker compose ps              # See service status
docker compose down            # Remove Compose containers and networks; preserve named volumes
docker compose down -v         # Also remove Compose-managed named volumes (and anonymous volumes)
docker compose up -d           # Recreate missing declared volumes
```

**Critical distinction:** `docker compose down -v` is destructive for database data in the removed volumes. If the Compose configuration still declares `postgres-data`, the next `up -d` creates a **new, empty** volume. PostgreSQL initializes a fresh database on that empty data directory. An external volume is not removed by `down -v`.

**Persistence test:**
1. POST notes to the API.
2. Run `docker compose down` (without `-v`).
3. Run `docker compose up -d`.
4. GET notes; the original records should still exist if the same volume/database is attached.

## 3. Docker networking and internal DNS

The Compose lab has two services on `notes-network`:

- `api`: Flask on container port 5000; host publishes port 8080.
- `db`: PostgreSQL on container port 5432; **no host port published**.

The API connects to **`db:5432`**, not `localhost:5432`:
- `db` is the Compose service name resolved by Docker's internal DNS on the shared user-defined network.
- `localhost` inside the API container refers to **the API container itself**.
- Publishing a host port is not required for containers on the same network to communicate.

```yaml
services:
  api:
    ports:
      - "8080:5000"
    environment:
      DB_HOST: db
    networks: [notes-network]
  db:
    image: postgres:16-alpine
    networks: [notes-network]
networks:
  notes-network:
    driver: bridge
```

### Verify network membership

```bash
docker network ls
docker network inspect docker-compose-lab_notes-network
# List attached container names only:
docker network inspect docker-compose-lab_notes-network \
  --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}'
```

The Compose project prefix varies. Get the actual name from `docker network ls`. Look for **both** API and DB containers in the network's `Containers` section.

### Verify PostgreSQL is not published on a host port

```bash
docker compose ps
docker compose port db 5432   # No published port should be reported
# Use the actual DB container name from docker compose ps:
docker inspect <db-container-name> --format '{{json .NetworkSettings.Ports}}'
```

`"5432/tcp": null` means no host port binding. `5432/tcp` in `docker ps` is **not** equivalent to `0.0.0.0:5432->5432/tcp`.

**Security nuance:** Not publishing the DB port reduces exposure, but does not replace credentials, network access controls, secret management, backups, or encryption.

## 4. Compose configuration, environment and healthchecks

Our lab uses `.env` for Compose variable substitution:

```env
DB_NAME=notesdb
DB_USER=notesuser
DB_PASSWORD=local-dev-password
```

The API receives `DB_HOST=db`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. The database receives `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.

```yaml
services:
  api:
    depends_on:
      db:
        condition: service_healthy
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 3s
      retries: 5
```

- `depends_on: condition: service_healthy` delays API startup until DB healthcheck passes; it is **not** a guarantee of correct application credentials or permanent availability.
- `pg_isready` checks whether the server accepts connections; it does **not** validate that the API password works.
- Do not commit `.env` secrets or paste password-bearing `docker compose config` output into public tickets.
- A `.dockerignore` excluding `.env` prevents it entering the Docker **build context**, but does not stop Compose from reading the project's `.env` file.

## 5. Troubleshooting workflow: inspect before changing

**Production-oriented order:**
1. Capture symptoms, impact, and exact error messages.
2. Check service/container status and logs.
3. Identify the failure layer: DNS, TCP/connectivity, authentication, application, or storage.
4. Inspect live container config, Compose config, networks, and mounts.
5. Make the smallest safe change; avoid deleting volumes.
6. Verify API endpoints and database records after the fix.

Useful commands:

```bash
docker compose ps
docker compose logs api
docker compose logs db
docker compose config               # Sensitive: may reveal secrets
docker network ls
docker volume ls
docker volume inspect <volume-name>
docker inspect <container-name>
curl http://localhost:8080/health
curl http://localhost:8080/notes
```

## 6. Scenario A — API fails PostgreSQL password authentication

**Symptom:**

```text
FATAL: password authentication failed for user "notesuser"
```

**Interpretation:** The API reached PostgreSQL, but authentication failed. PostgreSQL may still be `healthy` because `pg_isready` is not an API credential test.

**Investigate:**
- `docker compose ps`, `docker compose logs api`, `docker compose logs db`.
- Inspect `compose.yaml`, `.env`, and API environment-variable names/values **without exposing passwords**.
- Confirm API credentials match the credentials stored in the initialized database.

**Important PostgreSQL nuance:** For the official PostgreSQL image, `POSTGRES_PASSWORD` initializes the database user's password on first initialization of an empty data directory. Changing `.env` later **does not automatically reset** an existing PostgreSQL user's password in a persisted volume.

**Safe recovery:** If authorized and able to connect as an appropriate database role, rotate the actual PostgreSQL role password with `ALTER ROLE` (prefer an interactive secure method rather than placing a password in shell history), update the application's secret/configuration, and recreate only the API service:

```bash
docker compose up -d --no-deps --force-recreate api
```

Then verify service health and a real DB-backed API operation. **Do not run `down -v` to fix a password mismatch.**

## 7. Scenario B — Docker DNS resolution failure

**Symptom:**

```text
could not translate host name "db" to address:
Temporary failure in name resolution
```

**Interpretation:** The API could not resolve `db` to an IP address; this occurs **before** PostgreSQL authentication.

**Likely causes:** API and DB not on the same network; incorrect hostname; missing service/alias; transient DNS issue.

**Investigate:**

```bash
docker network ls
docker network inspect <network-name>
docker inspect <api-container-name>
docker inspect <db-container-name>
docker compose exec api getent hosts db
```

If the API container has exited or lacks `getent`, use a suitable diagnostic container attached to the same network or inspect network configuration first.

**Fix:** Ensure both services share `notes-network` and the API uses `DB_HOST=db`. Then apply the Compose changes with `docker compose up -d`; a full `down` is generally unnecessary. Verify DNS and API requests. No database volume deletion is required.

## 8. Scenario C — Records appear missing after deployment

**Example evidence:**

```text
docker volume ls:
  notes_postgres-data
  notes_postgres-data-backup

Current DB container mount:
  Name: notes_postgres-data-backup
  Destination: /var/lib/postgresql/data

Yesterday's DB mount:
  notes_postgres-data
```

**Likely diagnosis:** The new database container is mounted to a **different volume** than yesterday, so it may be reading a different database. The original records may still be safely stored in `notes_postgres-data`.

**Investigate without deleting data:**

```bash
docker compose ps
docker volume ls
docker volume inspect notes_postgres-data
docker volume inspect notes_postgres-data-backup
docker inspect <db-container-name> --format '{{json .Mounts}}'
docker compose config               # Review resolved volume mappings carefully
```

Review `compose.yaml`, project name changes, deployment scripts, and recent changes to the volume source. Confirm which database and schema the API is querying. If possible, inspect the original volume **read-only** in an isolated recovery environment and take backups before any change.

**Recovery approach:** After verifying that the original volume holds the expected data and arranging a controlled maintenance/recovery window, restore the DB service's mount to the correct original volume (or restore from a validated backup), preserving both volumes. Ensure no two independent PostgreSQL servers write to the same data directory. Validate record counts and API results before closing the incident.

**Lesson:** An empty API response does **not** prove a volume was deleted; it may indicate the wrong volume, database, schema, or query target.

## 9. Quick error classification for interviews

| Symptom | Likely layer | First checks |
|---|---|---|
| `could not translate host name db` | DNS | Service name, shared network, DNS test |
| `connection refused` | TCP/listener | DB process, listening port, readiness |
| `password authentication failed` | PostgreSQL auth | Credentials, persisted DB role password |
| API returns empty notes after deployment | Data/config | Mounted volume, DB name, schema, API target |
| DB container healthy, API unhealthy | Application dependency/config | API logs and real DB login |

## 10. Interview-ready answers

**Why volumes?** A container's writable layer is removed with the container; named volumes persist independently and can be reattached for stateful workloads.

**Why `db:5432`?** Docker's internal DNS resolves the Compose service name `db` on the shared network; `localhost` in the API container points back to the API container.

**Why no host port for PostgreSQL?** The API reaches it internally, so host publishing is unnecessary and would expand exposure.

**What does `down -v` do?** It removes Compose-managed named volumes as well as the stack. Recreating the stack may recreate empty volumes, but does not recover deleted records.

**What if API is recreated?** PostgreSQL data remains as long as the database's correct persistent volume remains attached and the API reconnects with correct configuration.

**What is the safest troubleshooting habit?** Diagnose the layer, inspect actual mounts/configuration, protect persistent data, make minimal changes, and verify end-to-end.

## 11. Hands-on verification checklist

- [ ] Start lab with `docker compose up -d --build`.
- [ ] Confirm both services with `docker compose ps`.
- [ ] Create and retrieve multiple notes.
- [ ] Inspect the network and identify both attached containers.
- [ ] Confirm DB has no published host port.
- [ ] Inspect PostgreSQL's named volume and mount destination.
- [ ] Run `docker compose down` (without `-v`), restart, and verify notes persist.
- [ ] Explain how DNS failure differs from authentication failure.
- [ ] Explain why changing `POSTGRES_PASSWORD` does not update an initialized DB.
- [ ] Diagnose a wrong-volume mount without deleting either volume.

---

**Safety reminder:** Never run `docker compose down -v`, `docker volume rm`, or destructive database commands against important data without a validated backup and explicit authorization.
