# 03 — Linux Disk & Filesystem Management

> **MAANG Prep · Week 1 · Day 3 · Block 1 (2 hours)**  
> **Original plan scope:** `df`, `du`, `mount`, `fdisk`, inodes, ext4 vs XFS.  
> **Goal:** Diagnose storage problems, manage filesystems safely, and explain production trade-offs in a DevOps/SRE interview.

## 1. Storage architecture

A typical Linux storage path is:

```text
Physical/virtual disk (/dev/sdb or /dev/nvme1n1)
  → partition table (GPT or MBR; optional)
  → partition (/dev/sdb1) or whole-disk filesystem
  → filesystem (ext4, XFS, etc.)
  → mount point (/data)
  → application files (/data/app.log)
```

- **Disk:** A block device (physical disk, EBS volume, etc.).
- **Partition:** A logical region of a disk. Partitioning is optional for some data volumes.
- **Filesystem:** Organizes files, directories, metadata, and storage blocks.
- **Mount point:** Directory through which a filesystem becomes accessible.
- **Important:** Attaching a disk does **not** partition, format, or mount it automatically.

## 2. `df` vs `du`

| Command | What it answers | Examples |
|---|---|---|
| `df` | How full is the filesystem? | `df -h`, `df -hT /data`, `df -i` |
| `du` | Which files/directories consume space? | `du -sh /var/log`, `du -xhd1 /var` |

```bash
# Filesystem space, type, inode usage
df -h
df -hT
df -i

# Directory usage (GNU/Linux)
sudo du -sh /var/log
sudo du -xhd1 /var | sort -h
sudo du -ah /var/log | sort -rh | head -20
```

- `df -h`: human-readable filesystem capacity, used space, available space.
- `df -i`: inode count and inode utilization.
- `du -s`: summary; `-h`: human-readable; `-x`: stay on one filesystem; `-d 1`: limit directory depth (GNU `du`).
- `df` and `du` can disagree because of deleted-but-open files, hidden files under mount points, filesystem metadata, reserved blocks, or measurement differences.

**Deleted-but-open files:** A process can retain a file descriptor after the file is unlinked, keeping disk blocks allocated until the final reference closes.

```bash
sudo lsof +L1
```

Do not blindly kill processes or remove active application files; investigate and use safe rotation/restart procedures.

## 3. Mounting and `/etc/fstab`

Mount an **existing** filesystem (example only; verify device and data first):

```bash
lsblk -f
sudo mkdir -p /data
sudo mount /dev/sdb1 /data
findmnt /data
df -hT /data
sudo umount /data
```

- `mount` attaches a filesystem to the directory tree.
- `umount` detaches it; it may fail when files are open or a process is using the mount.
- `findmnt` shows mounted filesystems and mount details.
- Mounting a filesystem over a nonempty directory temporarily hides the directory's existing contents until unmounted.
- A manual mount does not normally persist across reboot.

### Persistent mount with UUID

```bash
sudo blkid /dev/sdb1
```

Example `/etc/fstab` line (**replace the sample UUID**):

```fstab
UUID=abcd-1234  /data  ext4  defaults,nofail  0  2
```

| Field | Meaning |
|---|---|
| `UUID=...` | Stable filesystem identifier |
| `/data` | Mount point |
| `ext4` | Filesystem type |
| `defaults,nofail` | Mount options; `nofail` tolerates an absent optional volume at boot |
| `0` | Legacy dump field |
| `2` | fsck order (commonly non-root ext filesystems) |

```bash
sudo findmnt --verify
sudo systemctl daemon-reload  # on systemd-based systems after fstab changes
sudo mount -a                 # test carefully
findmnt /data
```

**Interview point:** Prefer UUID over `/dev/sdb1` for persistence because device names can change after reboot or reattachment. `nofail` prevents some boot failures but does not make an application independent of its required storage.

## 4. Partitioning: `fdisk`, GPT vs MBR

| Property | MBR | GPT |
|---|---|---|
| Traditional maximum with 512-byte sectors | ~2 TiB | Much larger |
| Typical partition layout | Four primary, or extended/logical scheme | Often 128 entries by default |
| Partition table redundancy | No backup table | Primary and backup tables |
| Integrity protection | No partition-table CRC | CRC checks |
| Typical new deployment choice | Legacy compatibility | Preferred for modern deployments |

**Do not confuse partition tables with filesystems:** GPT/MBR describe partition layout; ext4/XFS organize file data.

Useful commands:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
lsblk -f
sudo fdisk -l
sudo parted -l
sudo blkid
sudo wipefs -n /dev/sdb  # inspect signatures, non-destructive
```

### Safe lab: new, disposable 20 GB disk

> **DANGER:** `fdisk` writes partition tables and `mkfs` destroys existing filesystem contents. Never run these commands against your root disk, a production disk, or a device you have not positively identified. Take a snapshot/backup where applicable.

1. Verify the new empty device against cloud/VM attachment details and `lsblk`, `fdisk -l`, `wipefs -n`.
2. On the **verified empty lab disk only**, start `sudo fdisk /dev/sdb`.
3. In `fdisk`: `p` inspect; `g` create GPT; `n` new partition; accept suitable start/end; `p` review; `w` commit. **Do not use `w` if anything is unexpected.**
4. Ask kernel to reread table if needed: `sudo partprobe /dev/sdb`; inspect `lsblk` again.
5. Format the **new partition only**: `sudo mkfs.ext4 /dev/sdb1`.
6. Mount: `sudo mkdir -p /data && sudo mount /dev/sdb1 /data`.
7. Verify with `findmnt /data` and `df -hT /data`; configure `/etc/fstab` using actual UUID.

**AWS nuance:** On Nitro EC2 instances, EBS devices commonly appear as `/dev/nvme...`, not `/dev/sdb`. Always verify device identity; do not assume names.

## 5. Inodes and hard links

An **inode** stores metadata such as type, mode/permissions, owner, size, timestamps, link count, and data-block mapping. **It does not normally store the filename**; directory entries map names to inode numbers.

```bash
ls -li app.log
stat app.log

echo hello > original.txt
ln original.txt hardlink.txt
ls -li original.txt hardlink.txt
```

- A hard link is another directory entry referring to the **same inode** on the same filesystem.
- Removing one hard link does not free the inode/data while other links (or open references) remain.
- A symbolic link is a separate inode containing a path reference.

### Inode exhaustion

Symptom: `No space left on device` even when `df -h` shows free space.

```bash
df -h
df -i
sudo du --inodes -x -d 2 /var | sort -nr | head -20  # GNU/Linux
```

**Why?** On ext4, creating a new file generally needs an available inode as well as space for its data. Millions of tiny files can exhaust inodes before data blocks.

**Safe response:**

1. Confirm the affected filesystem and inode usage with `df -i`.
2. Locate inode-heavy directory trees; identify the owning application.
3. Remove **only** approved disposable files through supported cleanup/retention processes, if allowed.
4. If files cannot be removed, evaluate ext4 growth or migration to a filesystem with a better inode configuration.
5. Add inode usage alerts, retention controls, and capacity planning.

### Critical nuance: growing ext4 and inodes

- Expanding the EBS volume **alone** does not expand the filesystem or inode count.
- After extending the underlying partition/LV as needed, growing ext4 using `resize2fs` can add block groups and **increase the total number of inodes**.
- The filesystem's original inode density is not freely adjustable in place; additional inodes from growth may be insufficient for an unusually small-file-heavy workload.
- Alternative: provision a **new** ext4 filesystem with suitable inode density (for example, `mkfs.ext4 -i 4096` on a **new empty device**) and migrate data safely; or evaluate XFS.
- Never run `mkfs` on the existing filesystem to fix inode exhaustion.

## 6. ext4 vs XFS

| Topic | ext4 | XFS |
|---|---|---|
| Journaling | Yes | Yes |
| Inodes | Usually set up at filesystem creation; growth can add more | Allocated dynamically, within filesystem constraints |
| Online filesystem growth | Yes | Yes |
| Shrinking | Supported **offline**, with care | **Not supported** |
| Growth command | `resize2fs /dev/DEVICE` | `xfs_growfs /mountpoint` |
| Repair/check | `e2fsck` (normally unmounted) | `xfs_repair` (normally unmounted) |
| Typical use | General-purpose Linux workloads | Large filesystems, parallel I/O; workload-dependent |

Neither filesystem is universally faster; benchmark the actual workload and account for operational constraints.

### Growing storage safely

For an EBS expansion from 100 GB to 200 GB:

```bash
lsblk -f
df -hT
```

1. Confirm the correct EBS volume and take a snapshot/backup as appropriate.
2. Expand the cloud volume.
3. Expand the partition **if the filesystem is on a partition** (e.g., with `growpart`), or expand the LV if using LVM. Skip partition growth for a filesystem directly on the whole disk.
4. Grow the filesystem:

```bash
# ext4 example, after underlying block device is enlarged
sudo resize2fs /dev/sdb1

# XFS example, while mounted at /data, after underlying storage is enlarged
sudo xfs_growfs /data
```

5. Verify with `df -hT`, `df -i`, and `lsblk`.

**Shrinking:** ext4 shrinking requires unmounting and careful checks; XFS cannot be shrunk. Both are risky capacity operations and should be planned with backups.

## 7. Production troubleshooting playbook

### Scenario A: Root filesystem 98% full

```bash
df -hT
df -i
sudo du -xhd1 /var | sort -h
sudo du -xhd1 /var/log | sort -h
sudo lsof +L1
```

- Identify whether the issue is blocks, inodes, deleted-open files, logs, caches, or application data.
- Choose safe mitigation: log rotation, approved cache cleanup, or volume/filesystem expansion.
- Avoid deleting databases, live container storage, or arbitrary logs.
- Add alerts, log retention, and headroom thresholds.

### Scenario B: EBS disk is larger but `df` is unchanged

- Check `lsblk` vs `df -hT`.
- Determine whether the partition/LV and filesystem have also been grown.
- Grow the appropriate layer(s), then recheck.
- **Interview distinction:** disk size ≠ partition size ≠ filesystem size.

### Scenario C: Disk not mounted after reboot

```bash
lsblk -f
findmnt /data
sudo blkid
sudo findmnt --verify
journalctl -b -p warning
```

- Check EBS attachment, device mapping, actual UUID, `/etc/fstab` entry, mount point, and mount errors.
- Do not format a disk simply because it fails to mount.

### Scenario D: Kubernetes node reports `DiskPressure`

```bash
kubectl describe node NODE_NAME
kubectl get pods -A -o wide
# On the affected node:
df -hT
df -i
sudo du -xhd1 /var/lib | sort -h
```

- Investigate image layers, container logs, writable layers, and kubelet-managed ephemeral storage.
- Distinguish nodefs/imagefs/containerfs signals where supported by the runtime.
- Use Kubernetes/runtime-supported garbage collection and log rotation. **Never blindly delete files under `/var/lib/containerd` or `/var/lib/kubelet`.**

## 8. Interview Q&A — concise model answers

**Q1. `df` vs `du`?**  
`df` reports filesystem capacity/usage; `du` walks files and directories to estimate their usage. They may differ because of open deleted files and filesystem accounting.

**Q2. `df -h` shows free space, but `touch` says `No space left on device`. Why?**  
Check `df -i` for inode exhaustion; also investigate quotas and other filesystem-specific constraints.

**Q3. Why use UUID in `/etc/fstab`?**  
Device names can change; UUID provides a stable reference to a particular filesystem.

**Q4. MBR vs GPT for a 4 TB disk?**  
Usually GPT: traditional MBR with 512-byte sectors cannot represent the whole disk, and GPT supports more partitions and redundant metadata.

**Q5. Does enlarging an EBS volume automatically increase `df` capacity?**  
No. Grow the partition/LV if necessary, then the filesystem.

**Q6. Can you increase inodes on an ext4 filesystem without deleting files?**  
Growing ext4 can add inodes as new block groups are added. If inode density remains unsuitable, migrate to a newly created filesystem configured for the workload.

**Q7. Can ext4 and XFS be shrunk?**  
Ext4 supports offline shrinking; XFS does not support shrinking.

**Q8. How would you troubleshoot `DiskPressure` in Kubernetes?**  
Inspect node conditions/events, disk and inode usage, logs/images/ephemeral storage, then apply supported cleanup or capacity changes.

**Q9. Why can `df` report much more used space than `du`?**  
A deleted-but-open file may retain allocated blocks. Investigate with `sudo lsof +L1`.

**Q10. What do you do first when an unfamiliar disk appears on a server?**  
Inspect and verify its identity, signatures, existing partitions, mounts, and cloud attachment metadata before any writes.

## 9. Practical completion checklist

- [ ] Explain disk → partition → filesystem → mount point.
- [ ] Run and interpret `df -hT`, `df -i`, and `du -xhd1`.
- [ ] Explain why `df` and `du` may disagree.
- [ ] Use `lsblk`, `blkid`, `findmnt`, and `fdisk -l` safely.
- [ ] Explain UUID-based `/etc/fstab` and validate a sample entry.
- [ ] Compare MBR and GPT, including the traditional ~2 TiB MBR limit.
- [ ] Create GPT partition + ext4 filesystem on a **disposable** lab disk.
- [ ] Diagnose inode exhaustion without deleting required files.
- [ ] Explain ext4 vs XFS growth, shrinking, and inode differences.
- [ ] Walk through an EBS expansion and a Kubernetes `DiskPressure` incident.

## 10. What to study next

**This completes the Day 3 Block 1 topics in the original 5-week plan.** Don't spend more time on filesystem internals unless a lab or interview answer reveals a specific gap. A useful optional extension later is LVM (`pvcreate`, `vgcreate`, `lvcreate`), RAID, quotas, and deeper filesystem recovery; these are **not required topics listed in this block**.
---