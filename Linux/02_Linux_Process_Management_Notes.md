# Day 2 — Block 1: Linux Process Management

> MAANG / DevOps / SRE interview preparation. Commands are primarily for Linux with systemd; macOS differences are noted where relevant.

## Learning objectives

Understand how processes are created, observed, scheduled, signaled, supervised, and troubleshot. Connect Linux process behavior to Docker, Kubernetes, production incidents, and interview questions.

## 1. Process fundamentals

A **process** is a running instance of a program. A process has a PID, parent PID (PPID), user/group identity, execution state, open file descriptors, memory mappings, and scheduling attributes.

| Term | Meaning |
|---|---|
| PID | Process ID |
| PPID | Parent process ID |
| UID/GID | User/group identity |
| PGID | Process group ID; useful for job control and signaling groups |
| SID | Session ID |
| TTY | Controlling terminal, if any |
| STAT | Process state and modifiers |

```bash
ps -ef
ps -ef --forest
pstree -p
ps -p 1234 -o pid,ppid,user,stat,ni,%cpu,%mem,etime,cmd
```

On most systemd-based Linux systems, **PID 1** is `systemd`. PID 1 also has special responsibilities around adopting/reaping orphaned descendants; subreapers may also adopt them.

## 2. Foreground/background jobs and shell job control

- **Foreground:** attached to the terminal; shell waits for completion.
- **Background:** launched with `&`; shell returns to a prompt.
- **Stopped job:** typically suspend a foreground job using `Ctrl+Z` (SIGTSTP).

```bash
sleep 300 &       # launch in background
jobs -l           # jobs known to current shell
fg %1             # bring job 1 to foreground
bg %1             # resume stopped job 1 in background
```

`jobs`, `fg`, and `bg` operate on **shell jobs**, not arbitrary system PIDs. `Ctrl+C` sends SIGINT to the foreground process group. `Ctrl+Z` normally sends SIGTSTP.

## 3. Keeping processes running: nohup and alternatives

```bash
nohup ./script.sh > script.log 2>&1 &
```

`nohup` arranges for SIGHUP to be ignored so the program can often survive terminal disconnection. It is **not** a process supervisor: it does not automatically restart failed programs. For production daemons, prefer a service manager such as systemd. `tmux`/`screen` are alternatives for persistent interactive sessions.

## 4. Inspecting processes: ps, pgrep, pstree

```bash
ps                  # current shell's terminal-associated processes
ps -e               # all processes
ps -A               # all processes
ps -ef              # full-format listing
ps aux              # BSD-style listing
ps -u username      # processes for user
ps -G groupname     # processes by real group
ps -p 1234          # particular PID
ps -l -p 1234       # long-format listing for PID
ps -eo pid,ppid,stat,ni,%cpu,%mem,cmd --sort=-%mem | head
pgrep -af nginx
pstree -ap
```

Common columns: `PID`, `PPID`, `USER`, `%CPU`, `%MEM`, `VSZ` (virtual size), `RSS` (resident memory), `TTY`, `STAT`, `TIME` (accumulated CPU time), `CMD`.

**Interview nuance:** `ps aux` and `ps -ef` use different formatting conventions. `ps` is generally a snapshot; use `top`/`htop` for ongoing observation. A `grep` search may show the grep command itself; `pgrep` avoids that pattern.

## 5. Monitoring live processes: top and htop

```bash
top
top -p 1234
htop
```

Useful `top` indicators:

| Indicator | Interpretation |
|---|---|
| `us` | CPU time in user space |
| `sy` | CPU time in kernel space |
| `id` | Idle CPU time |
| `wa` | CPU time waiting for I/O (interpret with workload context) |
| `st` | Stolen CPU time on a virtualized host |
| Load average | Average runnable or uninterruptible tasks, **not** CPU percentage |

Common interactive `top` keys: `P` sort CPU, `M` sort memory, `k` signal a process, `q` quit. `htop` offers a more interactive process tree and filtering interface but may not be installed.

**Load average:** compare 1-, 5-, and 15-minute values with the number of available CPUs and examine I/O wait and blocked tasks before concluding CPU saturation.

## 6. Signals, kill, pkill, killall

`kill` **sends a signal**; it does not always mean immediate termination.

```bash
kill -l                 # list signals
kill 1234               # default SIGTERM (15)
kill -TERM 1234          # request graceful termination
kill -15 1234            # same signal
kill -KILL 1234          # force termination
kill -9 1234             # same signal
kill -HUP 1234           # SIGHUP; app-specific behavior
kill -STOP 1234          # stop (cannot be caught)
kill -CONT 1234          # continue
pkill -TERM -f 'my-app'
```

| Signal | Number (common Linux) | Meaning |
|---|---:|---|
| SIGINT | 2 | Interrupt, often Ctrl+C |
| SIGQUIT | 3 | Quit; may produce core dump |
| SIGHUP | 1 | Hangup; **some** daemons interpret as reload |
| SIGKILL | 9 | Forced kill; cannot be caught or ignored |
| SIGTERM | 15 | Graceful termination request; catchable |
| SIGSTOP | 19 on many Linux architectures | Stop; cannot be caught |
| SIGCONT | 18 on many Linux architectures | Resume |

Signal numbers can differ by architecture/OS: use names for portability. `kill -1` **does not universally restart** a service. Prefer `systemctl reload SERVICE` when supported or `systemctl restart SERVICE` when a restart is required. SIGKILL prevents application cleanup; try SIGTERM first. A task in uninterruptible kernel sleep may not disappear immediately even after SIGKILL.

## 7. Process states, zombies, and orphans

| State | Meaning |
|---|---|
| `R` | Running or runnable |
| `S` | Interruptible sleep |
| `D` | Uninterruptible sleep, often waiting in kernel for I/O |
| `Z` | Zombie: exited child whose status has not been reaped |
| `T` | Stopped/traced |
| `I` | Idle kernel thread on some Linux versions |

**Zombie:** the child **has exited**, but the parent has not called a wait-family function to collect exit status. The parent can still be alive. A zombie no longer consumes normal application CPU/memory, but retains a process table entry until reaped.

**Orphan:** a child is **still running** when its parent exits. It is reparented to an appropriate subreaper or PID 1.

**D-state:** task waits in an uninterruptible kernel operation, often storage/network filesystem I/O. SIGKILL may remain pending until it returns to a signal-handling point. Diagnose underlying I/O/storage issues instead of repeatedly issuing `kill -9`.

```bash
ps -eo pid,ppid,stat,wchan:30,cmd | grep -E '(^| )D|(^| )Z'
```

## 8. Scheduling priorities: nice and renice

Under ordinary Linux scheduling, **nice values** run from `-20` (higher scheduling priority) to `+19` (lower priority). Default is typically `0`.

```bash
nice -n 5 ./batch-job.sh
sudo nice -n -10 ./important-job.sh
renice -n 10 -p 1234
ps -p 1234 -o pid,ni,pri,cmd
```

Increasing priority (lowering nice value) generally requires elevated privileges. `nice` is a relative scheduling weight, **not** a hard CPU cap or guarantee. Real-time policies, CPU affinity, cgroup limits, and CPU contention also matter.

## 9. systemd and systemctl

On many Linux distributions, `systemd` is the init and service manager. It manages units such as `.service`, `.socket`, `.timer`, `.target`, `.mount`, and `.path`.

```bash
systemctl status nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo systemctl enable nginx
sudo systemctl enable --now nginx
sudo systemctl disable nginx
systemctl is-enabled nginx
systemctl is-active nginx
sudo systemctl mask nginx
sudo systemctl unmask nginx
systemctl list-units --type=service
systemctl list-unit-files --type=service
systemctl list-sockets
```

**Critical distinctions:**

- `start` starts **now**; `enable` configures startup via unit installation dependencies (commonly boot). `enable --now` does both.
- `disable` does **not** stop a running service; a disabled service may still be manually started or triggered by dependencies.
- `mask` prevents ordinary activation by linking the unit to `/dev/null`; unmask before starting. Masking does not necessarily stop an already running service.
- `reload` requests configuration reload if supported; `restart` stops/starts the unit.
- After editing unit definitions, run `sudo systemctl daemon-reload`.

Example service unit (`/etc/systemd/system/example-app.service`):

```ini
[Unit]
Description=Example application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/example-app
ExecStart=/usr/bin/python3 /opt/example-app/app.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now example-app
systemctl status example-app
journalctl -u example-app -n 100 --no-pager
journalctl -u example-app -f
journalctl _PID=1234 -n 100
systemctl show example-app -p Result -p ExecMainCode -p ExecMainStatus -p NRestarts
```

`Restart=on-failure` is a policy, not an unconditional promise of recovery; start limits and failure types can affect behavior. Inspect `systemctl cat SERVICE` and `systemctl show SERVICE` for effective configuration.

Host control on systemd Linux: `systemctl reboot`, `systemctl poweroff`. Be cautious with inhibitor bypass options; do not use them casually on production systems.

## 10. cron and crontab

Cron runs commands on a schedule. User crontabs commonly have **five time fields**, then a command:

```text
minute hour day-of-month month day-of-week command
  *     *        *         *        *
```

```bash
crontab -e   # edit current user's crontab
crontab -l   # list
crontab -r   # remove (destructive)
```

Examples:

```cron
*/5 * * * * /usr/local/bin/healthcheck.sh >> /var/log/healthcheck.log 2>&1
0 2 * * * /usr/local/bin/backup.sh
0 9 * * 1 /usr/local/bin/weekly-report.sh
0 0 28 2 * /usr/local/bin/february-task.sh
```

**Common production failures:** minimal `PATH`, wrong working directory, permissions, absent executable bit, missing environment variables, time-zone/DST assumptions, overlapping jobs, or discarded output. Use absolute paths and explicit logging. Be aware that day-of-month and day-of-week matching has special OR semantics in common cron implementations when both are restricted. `/etc/crontab` and `/etc/cron.d/*` commonly add a **user** field not present in user crontabs.

**Cron vs systemd timers:** cron is compact and ubiquitous; systemd timers integrate with service units, dependencies, logging, missed-run behavior (e.g. `Persistent=true` with calendar timers), and resource controls. Choose based on environment and requirements.

## 11. Processes vs threads

A process owns a resource context; threads within it share much of that context (e.g. address space) while retaining separate execution state. High thread count can create memory/scheduling pressure.

```bash
ps -eLf | head
top -H -p 1234
ls /proc/1234/task/     # Linux threads for PID
```

## 12. The /proc filesystem and file descriptors

`/proc` is a virtual Linux filesystem exposing kernel/process state. It is not a normal persistent on-disk directory.

```bash
cat /proc/1234/status
tr '\0' ' ' < /proc/1234/cmdline
ls -l /proc/1234/fd
cat /proc/1234/limits
cat /proc/1234/oom_score
cat /proc/1234/oom_score_adj
lsof -p 1234
ulimit -n
```

Useful files include `status`, `stat`, `cmdline`, `environ` (may contain secrets; handle carefully), `fd/`, `maps`, `limits`, and `task/`. Access can be restricted by permissions and process isolation. Too many open files can cause failures; inspect per-process limits and descriptors.

## 13. Memory pressure and OOM Killer

A high `%MEM` reading alone does not prove a leak. Distinguish application RSS, page cache, reclaimable memory, swap, memory pressure, and cgroup limits.

```bash
free -h
vmstat 1
ps aux --sort=-%mem | head -15
journalctl -k --no-pager | grep -iE 'oom|out of memory|killed process'
dmesg -T | grep -iE 'oom|out of memory|killed process'
```

The Linux OOM killer may terminate processes when memory cannot be satisfied. `oom_score` and `oom_score_adj` affect victim selection, but cgroup OOM behavior and other factors matter. In Kubernetes, inspect pod events, container `lastState.terminated.reason`, memory limits, and node pressure. **Exit code 137 indicates SIGKILL (128+9), not necessarily OOM by itself.**

## 14. Namespaces and cgroups: Docker/Kubernetes connection

**Namespaces** isolate a process's view of resources: PID, network, mount, UTS, IPC, user, and cgroup namespaces. **Cgroups** account for and limit resource use (CPU, memory, PIDs, I/O, etc.).

- A containerized process may see itself as PID 1 within its **PID namespace**, while the host sees a different PID.
- Ordinary Linux containers **share the host kernel**; they do not each run a separate kernel.
- Docker Desktop on macOS typically uses a Linux VM to provide that Linux kernel; containers inside the VM share its kernel.
- Kubernetes `requests` influence scheduling and CPU shares; `limits` constrain use (memory limits can cause OOM kills, CPU limits can cause throttling).
- A container's PID 1 should handle signals and reap child processes; an init wrapper such as `tini` can help.

```bash
docker top CONTAINER
kubectl describe pod POD -n NAMESPACE
kubectl logs POD -n NAMESPACE --previous
kubectl top pod POD -n NAMESPACE
```

## 15. CPU affinity and hard resource limits

```bash
taskset -cp 1234
sudo taskset -cp 0,1 1234
ulimit -a
systemctl show example-app -p CPUQuota -p MemoryMax -p TasksMax
```

- `nice`: relative CPU scheduling priority.
- `taskset`: CPU affinity, not a quota.
- cgroup/systemd CPU quotas: enforce CPU consumption limits over periods.
- `ulimit`: shell/process resource limits (not a full replacement for cgroups).

## 16. Production incident playbooks

### A. High CPU

```bash
uptime
top
ps -eo pid,ppid,stat,%cpu,%mem,cmd --sort=-%cpu | head -15
top -H -p PID
```

Check whether load is CPU-bound or due to I/O-blocked tasks; correlate with recent deployments, traffic, thread counts, logs, and metrics. Avoid immediately killing the process without checking service impact.

### B. App unresponsive, memory 98%, CPU 20%, service failed

```bash
free -h
uptime
top
ps aux --sort=-%mem | head -10
systemctl status SERVICE
journalctl -u SERVICE -n 100 --no-pager
sudo journalctl -k --no-pager | grep -iE 'oom|out of memory|killed process'
systemctl show SERVICE -p Result -p ExecMainCode -p ExecMainStatus -p NRestarts
```

Investigate memory pressure, swap, service logs, OOM evidence, cgroup/container limits, and app-specific memory behavior (e.g. JVM heap vs native memory). Stabilize safely; prevent recurrence through leak fixes, right-sizing, alerting, memory tuning, and workload controls.

### C. Service will not start

```bash
systemctl status SERVICE
journalctl -u SERVICE -b -n 100 --no-pager
systemctl cat SERVICE
systemctl is-enabled SERVICE
```

Check unit configuration, executable path, working directory, permissions, dependencies, ports, environment, resource limits, and start-limit failures. If masked, unmask deliberately before starting.

### D. Process appears stuck in D-state

```bash
ps -p PID -o pid,ppid,stat,wchan:32,cmd
dmesg -T | tail -80
```

Inspect storage/NFS/kernel logs, I/O latency, and blocked tasks. SIGKILL may not take effect until the kernel wait completes.

### E. Cron job runs manually but fails in cron

Check schedule syntax, execution user, absolute paths, PATH/environment, working directory, permissions, logging, and concurrent execution. Test under a similarly minimal environment.

### F. Kubernetes pod repeatedly restarts

```bash
kubectl describe pod POD -n NAMESPACE
kubectl logs POD -n NAMESPACE --previous
kubectl get pod POD -n NAMESPACE -o yaml
```

Check termination reason, exit code, probes, memory limits, application errors, deployment changes, and node events. Distinguish `OOMKilled`, probe-triggered restarts, and generic SIGKILL.

## 17. Linux vs macOS caveats

- macOS uses **launchd**, not systemd; `systemctl`, `journalctl`, and `/proc` are not native macOS tools.
- `ps`, `top`, `nice`, and `kill` exist on macOS but flags/output may differ from GNU/Linux.
- Linux-specific tools such as `taskset`, `free`, and many `/proc` workflows generally require a Linux environment.
- For hands-on practice, use a Linux VM, cloud VM, or suitable Linux container (noting containers may lack systemd).

## 18. Compact command cheat sheet

| Goal | Command |
|---|---|
| List all processes | `ps -ef` |
| Process tree | `pstree -p` |
| Find PID by name | `pgrep -af NAME` |
| Inspect PID | `ps -p PID -o pid,ppid,stat,ni,%cpu,%mem,cmd` |
| Live process view | `top` / `htop` |
| Threads | `top -H -p PID` |
| Graceful signal | `kill -TERM PID` |
| Force kill | `kill -KILL PID` |
| Start lower-priority job | `nice -n 10 COMMAND` |
| Change priority | `renice -n 10 -p PID` |
| Keep command across logout | `nohup COMMAND > app.log 2>&1 &` |
| Start service | `sudo systemctl start SERVICE` |
| Enable and start | `sudo systemctl enable --now SERVICE` |
| Service logs | `journalctl -u SERVICE -n 100` |
| Edit cron | `crontab -e` |
| Memory snapshot | `free -h` |
| Kernel OOM evidence | `journalctl -k` |
| Open descriptors | `ls -l /proc/PID/fd` |

## 19. Hands-on practice checklist

- [ ] Launch `sleep 300 &`, inspect `jobs -l`, move it with `fg` and `bg`.
- [ ] Find a process using `ps`, `pgrep`, and `pstree`.
- [ ] Inspect CPU, memory, state, priority, and elapsed time with custom `ps -o`.
- [ ] Compare `top` and `htop`; identify CPU vs memory leaders.
- [ ] Send SIGTERM to a disposable test process; compare with SIGKILL only in a safe lab.
- [ ] Launch a low-priority CPU-intensive test and inspect nice values.
- [ ] Create a minimal systemd service on a disposable Linux VM and inspect its journal.
- [ ] Add a harmless cron entry writing timestamps to a file; debug PATH and output.
- [ ] Inspect `/proc/$$/status`, `/proc/$$/limits`, and `/proc/$$/fd` on Linux.
- [ ] Examine a Docker container's PID namespace and process view.
- [ ] Practice the memory-pressure incident playbook with mock logs/metrics.

## 20. Interview questions and model-answer pointers

1. **What is the difference between a process and a thread?** Address isolation, shared memory, scheduling, and failure implications.
2. **What does `kill -9` do?** SIGKILL cannot be caught; cleanup is bypassed; D-state caveat.
3. **Zombie vs orphan?** Zombie exited but unreaped; orphan still running after parent exits.
4. **`systemctl start` vs `enable`?** Immediate activation vs startup configuration.
5. **`disable` vs `mask`?** Disable autostart linkage vs block ordinary activation.
6. **Why does a cron script fail when it works interactively?** Environment, paths, user, permissions, time zone, logging.
7. **How does `nice` differ from CPU limits?** Relative scheduler weight vs enforced quota.
8. **Why can a container process have PID 1?** PID namespace view; shared host kernel.
9. **Does exit code 137 prove OOM?** No; SIGKILL can have other causes; seek corroboration.
10. **How do you investigate high load with low CPU usage?** Check D-state tasks, I/O waits, blocked processes, and storage/network filesystem issues.
11. **How do you troubleshoot a failed systemd service?** `status`, `journalctl`, unit config, exit status, dependencies, permissions, limits.
12. **How do you distinguish a memory leak from normal Linux page cache?** Correlate RSS/cgroup usage, reclaimability, swap, OOM logs, and time-series trends.

## 21. Quick self-check: prior quiz corrections

- **Q4 (systemd and cron):** Correct choice **B**: `systemctl enable`, `Restart=on-failure`, and `0 2 * * *` for 2:00 AM daily (subject to service/unit context).
- **Q5 (Docker/Kubernetes):** Correct choice **B**: PID namespaces provide different PID views. The choice claiming each Linux container has a separate kernel is incorrect.

## Completion criteria

You should be able to explain process states, signals, jobs, priorities, systemd, cron, OOM, `/proc`, namespaces, and cgroups **without memorizing only commands**, and work through a production incident with an evidence-first troubleshooting sequence.

## 22. Detailed model answers to the 12 interview questions

### Q1. Process vs thread
A **process** has its own virtual address space and resource context. **Threads** within one process share that address space and many resources, but have separate stacks, registers, and execution states. Linux schedules threads individually. Threads are efficient for concurrent work but require synchronization to avoid races and deadlocks. A fatal fault in one thread can terminate the entire process.

```bash
ps -eLf
top -H -p 1234
```

### Q2. What does `kill -9` do?
`kill -9 PID` sends **SIGKILL**, which cannot be caught, blocked, or ignored; application-level shutdown handlers cannot run. Prefer `kill -TERM PID` (or `systemctl stop SERVICE`) first to permit graceful cleanup. A process stuck in uninterruptible kernel sleep (`D`) may not disappear until the kernel operation returns.

### Q3. Zombie vs orphan
A **zombie** has already exited, but its parent has not collected the exit status using `wait()` or related calls. The parent can still be alive. An **orphan** is still running after its parent exits and is reparented to a subreaper or PID 1. Sending SIGKILL to a zombie cannot help; fix or terminate the parent if appropriate so the child can be reaped.

```bash
ps -eo pid,ppid,stat,cmd
```

### Q4. `systemctl start` vs `enable`
`start` activates the service now; `enable` configures its activation through installation links, commonly on boot. A service can be running and disabled, or enabled and stopped. `systemctl enable --now nginx` does both.

### Q5. `disable` vs `mask`
`disable` removes enablement links but generally still permits manual or dependency-based activation. `mask` prevents ordinary activation by linking the unit to `/dev/null`. Neither command necessarily stops a service already running. Use `systemctl unmask NAME` before trying to start a masked service.

### Q6. Why does cron fail when the same script works interactively?
Cron usually has a smaller environment, limited `PATH`, different working directory, different identity or permissions, and possibly different time-zone assumptions. Use absolute paths, explicit interpreters, and output redirection; inspect cron logs and test under the cron job's user.

```cron
0 2 * * * /usr/bin/bash /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Q7. `nice` vs CPU limits
`nice` changes **relative CPU scheduling weight** under ordinary scheduling; it does not enforce a CPU cap. Nice values range from -20 (higher priority) to +19 (lower priority). A cgroup CPU quota, including a Kubernetes CPU limit, enforces an upper bound on CPU usage over time. A low-priority task can use an otherwise idle CPU.

### Q8. Why can a container process be PID 1?
PID namespaces give processes a container-local view of PIDs. A process may appear as PID 1 inside a container while having a different host PID. Linux containers share the host Linux kernel. Container PID 1 must be designed to handle signals and reap child processes appropriately.

```bash
docker exec my-container ps -ef
docker top my-container
```

### Q9. Does exit code 137 prove OOM?
No. **137 = 128 + 9** typically means termination by SIGKILL. OOM is one possible reason; manual SIGKILL and forced container termination are others. Corroborate with `reason: OOMKilled`, kernel logs, and memory metrics.

```bash
kubectl describe pod POD
kubectl get pod POD -o yaml
kubectl logs POD --previous
```

### Q10. High load average but low CPU utilization?
Linux load average includes runnable tasks **and** tasks in uninterruptible sleep. Many tasks blocked on slow disks, NFS, or other I/O can raise load while CPU remains mostly idle. Check process states, I/O wait, storage latency, and blocked call sites.

```bash
uptime
top
ps -eo pid,stat,wchan:30,cmd
vmstat 1
iostat -xz 1
```

### Q11. Troubleshoot a failed systemd service
First inspect status and journal, then inspect unit definition and exit details. Check config validity, permissions, dependencies, port conflicts, environment variables, and resource constraints. Collect evidence before restarting repeatedly. If the unit definition changes, run `daemon-reload` before restarting.

```bash
systemctl status nginx
journalctl -u nginx -n 100 --no-pager
systemctl cat nginx
systemctl show nginx -p Result -p ExecMainStatus -p NRestarts
sudo systemctl daemon-reload
sudo systemctl restart nginx
```

### Q12. Memory leak vs normal Linux page cache
Linux intentionally uses available memory for filesystem caching; much of that cache is reclaimable. A possible application memory leak shows sustained growth in process or cgroup memory that fails to stabilize under comparable load. Compare `MemAvailable`, RSS, swap/pressure, OOM logs, and time-series trends. RSS growth alone is not proof: allocators and legitimate application caches can also grow.

```bash
free -h
ps aux --sort=-rss | head
cat /proc/PID/status
cat /proc/meminfo
```

### Prior quiz answer key
- **Q4:** B — `systemctl enable`, `Restart=on-failure`, and `0 2 * * *`.
- **Q5:** B — PID namespaces provide different PID views; Linux containers do not each run a separate kernel.
