# Week 1, Day 1: Linux File System Hierarchy, Permissions, Users & Groups

## Why This Matters

As a DevOps or SRE engineer targeting MAANG-level roles, you need to navigate, troubleshoot, and secure Linux-based production environments instinctively and without a GUI. On your first day of preparation, mastering the standard file system layout and permissions model (`chmod`, `chown`, `umask`) ensures you can inspect configuration files, fix permission denied errors, and enforce security compliance swiftly.

---

## 1. Linux File System Hierarchy (`FHS`) 

Linux organizes everything as a file within a single, unified virtual file tree starting from the root directory (`/`). Understanding where files reside is critical for debugging logs, managing binaries, and configuring services.

*   **Root Directory (`/`)**: Virtual file tree starting point where all files, directories, and devices are mounted.
*   **User Home Directories**. 
    *   `/home`: Default location for individual regular user home directories (e.g., `/home/pinal`). -- Its like the personal workspace, every user gets its own home directory
    *   `/root`: Dedicated home directory for the administrative root user. -> its for the admin account 
*   **System Binaries & Executables**
    *   `/bin`: Essential command-line binaries required in single-user mode (e.g., `ls`, `cp`, `bash`, `mv`, `cat`, `mkdir`, etc). -> Its a toolbox which allow the linux to operate, whithout this system would be very helpful
    *   `/sbin`: Essential system administration binaries restricted primarily to the root user (e.g., `fdisk`, `iptables`). -> 
        *    s -stands for system, admin tools (`Networking : ip, ifconfig, route`, `Disk Management : fdisk, mkfs, parted`, `Booting the System : grub-install, init`, `System-Recovery : fsck, e2fsck`)
    *   `/usr/bin` & `/usr/sbin`: Non-essential user binaries, applications, and system utilities.
        *    usr - Unix System Resources >
*   **Configuration & State Files**
    *   `/etc`: System-wide configuration files (e.g., `passwd`, `fstab`, service configuration files like `nginx.conf`). ->Its like a Setting folder, store the config files like network setting, ssh, application, 
*   **Variable & Data Files**
    *   `/var`: Variable data files, including system logs (`/var/log`), mail spools, and temporary application caches.
        * whenever troubleshooting the linux -> this is the first place needs to check becuase it contains the log file like `/var/log/syslog`, `/var/mail`, `/var/lib`, `/var/spool`, `/var/cache`
*   **Kernel & Virtual Pseudo-Filesystems**
    *   `/proc`: Dynamic, in-memory virtual filesystem exposing kernel and process states as text files. -> /proc doesn't actually exist on hard disk, Its a virtual filesystem create by the Linux Kernel, It contains the live information about running processes, cpu usage, memory, system configuration and much more, whenever monitoring needs an info about memory it usese the `cat /proc/meminfo`,
        *   think of it like the live dashboard of the whats happening right now inside linux right now 
    *   `/boot`: It contains everything is needed to start linux, like The linux kerner, Bootloader files and the startup configuration all are lives here. without these files operating system can be boot or start.
    *   `/sys`: Virtual filesystem representing device and kernel configuration parameters.
    *   `/lib`: shared library are lives here 
    *   `/dev`: Special directory containing device nodes representing hardware components and pseudo-devices.
        *   In the linux almost everything is treated as file. like Mice, UsbDriver, printer, etc many more all are appere in the `/dev/` 
        *   for example Hard Drive appeare in the `ls -l /dev/sda` -> so it will allow the program to interact with the hardware with the same file based inteface and the regular files (open(), read(), write(), close())
        *   It is the one of reason linux is so flexible
    *   `/tmp`: temporaty files stored here 
*   **USB Driver**
    *   `/media`: When we plug in a USB Driver it shows like this and `/media` used for the automatically mounted
    *   `/mnt`: Manually mount the disk and generally used by the admin (`sudo mount /dev/sdb1 /mnt/backup`) -> so it will be like `mounted /dev/sdb1 on /mnt/backp` like wise

---
What lives where
*   `/home` -> User Files
*   `/bin /sbin /usr` -> Programs
*   `/etc` -> Configuration Files and looks like setting folder
*   `/lib` -> Shared Libraries
*   `/var` -> Logs and changing data -- `/var/lib`, `/var/logs/syslog`
*   `/tmp` -> temporary Files
*   `/dev` -> Hardware devices
*   `/mnt or /media` -> external storage
*   `proc` -> System Information
*   `boot` -> Boot Files
---

## 2. Linux Permissions and Ownership Model

    Use this link for more detailed info - `https://linuxhandbook.com/linux-file-permissions/`

Linux controls file access using user, group, and others (ugo) permissions combined with ownership flags and default permission limiters.

By design, Linux is a multi-user operating system. In an enterprise system, there would be multiple users accessing the same system. But if any user could access and modify all files belonging to other users or system files, this would certainly be a security risk.

This is why UNIX and thus Linux (Linux is a Unix-like system) has built-in security measure in place. This ensures that a file or directory can be accessed, modified or executed by only desired users.


*   **File Ownership (`chown`)stands for change the owner and (`chgrp` stands for change group)**
    *   **User Owner (`u`)**: User is the owner of the file. When you create a file, you become the owner of the file. The ownership can be changed as well.
    *   **Group Owner (`g`)**: A designated group of users sharing common access privileges. Every user is part of a certain group(s). A group consists of several users and this is one way to manage users in a multi-user environment.
        * For example, if you have dev team, QA team and sysadmin team accessing the same system, you should create separate groups for them. This way, you can manage files and security of the system effectively. It saves time because instead of manually adding permission for each user, you can simply add them to a group and change the permission for the group. You’ll see how to do it later in this article.
        * Even if you are the only user of the system, you’ll still be part of many groups. Distributions like Ubuntu also create a group with name same as the user’s name.
        * Run the command `groups` to see what user-groups you belong to.
    *   **Others (`o`)**: All other system users not captured by the owner or group.
        * ‘Other’ can be considered as a big group with all the users on the system. Basically, anyone with access to the system belongs to this group.
        * In other words, ‘User’ is a single user, Group is a collection of users and Other consists of all the users on the system.
    * **for all**
        * `a` = all (user + group + other)
    `chown <new_user_name> <filename>` -> to change the user owner
    `chown <new_user_name>:<new_user_group> <filename>` -> want to change the user as well as group
    `chown :<new_user_group> <filename>` -> just want to change the group
    `chgrp <new_user_group> <filename>` -> just want to change the group
    `sudo chown root:root test.txt` In our example so far, if you want to change the user owner and group to root, you can use the chown command like this:
    `-rw-rw---- 1 root root 457 Aug 10 11:55 test.txt`
    * **Notice that I had to use sudo with chown? It’s because the root is involved here and to deal with root, you need superuser rights.**

*   **Permission Types (`chmod`) full form change the mode of access**
    * ***Permissions for files***
        * Read – Can view or copy file contents
        * Write – Can modify file content
        * Execute – Can run the file (if its executable)
    * ***Permission for Directories or folders***
        * Read – Can list all files and copy the files from directory
        * Write – Can add or delete files into directory (needs execute permission as well)
        * Execute – Can enter the directory
    
    *   **Read (`r` = 4)**: Permission to view file contents or list directory contents.
    *   **Write (`w` = 2)**: Permission to modify/delete file contents or create/delete files inside a directory.
    *   **Execute (`x` = 1)**: Permission to run a file as a script/binary or traverse/enter a directory.


*   **Notation Systems**
    *   **Symbolic Notation**: Modifying permissions using letters and operators (e.g., `chmod u+x script.sh`). (+ for adding permissions, – for removing permissions, = for overriding existing permissions with new value)
    *   **Octal/Numeric Notation**: Using 3-digit octal codes representing the sum of owner, group, and other permission values (e.g., `chmod 755 app.py`).
*   **Default Masking (`umask`)**
    *   The permission mask subtracted from maximum defaults (666 for files, 777 for directories) to automatically secure newly created items.

---

Bonus Tip: Is there a precedence in file permissions?
Think of a situation, where the user owner doesn’t have any permissions, group has read permission while others have read and write permissions.

* `----r--rw- 1 Pina itsfoss 457 Aug 10 11:55 test.txt`
Now, if the user Pina tries to read the file using cat or less command, will he be able to? The answer is no because it doesn’t have the read permission.

But user Pina is part of group itsfoss and the group has read access. Heck! other has read and write permission. This should mean that everyone (including user Pina) can read and write the file, right? Wrong!

In Linux, the precedence takes from user and then group and then to other. Linux system checks who initiated the process (cat or less in our example). If the user who initiated the process is also the user owner of the file, the user permission bits are set.

If the owner of the file didn’t initiate the process, then the Linux system checks the group. If the user who initiated the process is in the same group as the owner group of the file, group permissions bit are set.

If this process owner is not even in the group as the file’s group owner, then the other permission bits are set.

---

`-rwxrw-r-- 1 Pinal itsfoss 457 Aug 10 11:55 test.txt`
* **File type**: Denotes the type of file. d means directory, – means regular file, l means a symbolic link.
* **Permissions**: This field shows the permission set on a file. I’ll explain it in detail in the next section.
* **Hard link count**: Shows if the file has hard links. Default count is one.
* **User**: The user who owns the files.
* **Group**: The group that has access to this file. Only one group can be the owner of a file at a time.
* **File size**: Size of the file in bytes.
* **Modification time**: The date and time the file was last modified.
* **Filename**: Obviously, the name of the file or directory.

`rwxrw-r--` -> `r` -> read, `w` -> write, `x` -> execute, `-` -> no permission set
* The file test.txt is owned by user Pinal and Pinal has read, write and execute permission. All the members of group istfoss have read and write access to this file while everyone else has only read access to this file.
---

## Special File Permissions in Linux: SUID, GUID and Sticky Bit

* File permissions and ownership are the basic and yet essential security concepts in Linux. You probably are already familiar with these terms already. It typically looks like this:
    * `rwxrw-r--`

* Apart from these regular permissions, there are a few special file permissions and not many Linux users are aware of it.
    * `rws rws rwt` -> lets seprate them
        * `rws` first chunk -> `rw` would be the same like read and write permission, `s` -> `SUID`: 
        * **What is SUID?** -> When the SUID bit is set on an executable file, this means that the file will be executed with the same permissions as the owner of the executable file.
            `linuxhandbook:~$ ls -l /usr/bin/passwd`
            `- rws r-x r-x 1 root root 59640 Mar 22  2019 /usr/bin/passwd`
        * This means that any user running the passwd command will be running it with the same permission as root.
        * What’s the benefit? The passwd command needs to edit files like /etc/passwd, /etc/shadow to change the password. These files are owned by root and can only be modified by root. But thanks to the setuid flag (SUID bit), a regular user will also be able to modify these files (that are owned by root) and change his/her password.

        * This is the reason why you can use the passwd command to change your own password despite of the fact that the files this command modifies are owned by root.

        * Why can a normal user not change the password of other users?
            * Note that a normal user can’t change passwords for other users, only for himself/herself. But why? If you can run the passwd command as a regular user with the same permissions as root and modify the files like /etc/passwd, why can you not change the password of other users?
            * If you check the code for the passwd command, you’ll find that it checks the UID of the user whose password is being modified with the UID of the user that ran the command. If it doesn’t match and if the command wasn’t run by root, it throws an error.
            * The setuid/SUID concept is tricky and should be used with utmost cautious otherwise you’ll leave security gaps in your system. It’s an essential security concept and many commands (like ping command) and programs (like sudo) utilize it.

    * Now that you understand the concept SUID, let’s see how to set the SUID bit.
        * **How to set SUID bit?** -> I find the symbolic way easier while setting SUID bit. You can use the chmod command in this way:
        * `chmod u+s file_name`  
            ```
            linuxhandbook:~$ ls -l test.txt
            -rwxrw-rw- 1 linuxhandbook linuxhandbook 0 Apr 12 17:51 test.txt
            linuxhandbook:~$ chmod u+s test.txt
            linuxhandbook:~$ ls -l test.txt
            -rwsrw-rw- 1 linuxhandbook linuxhandbook 0 Apr 12 17:52 test.txt
            ```
        * You can also use the numeric way. You just need to add a fourth digit to the normal permissions. `The octal number used to set SUID is always 4.`

            ```
            linuxhandbook:~$ ls -l test2.txt
            -rwxrw-rw- 1 linuxhandbook linuxhandbook 0 Apr 12 17:53 test2.txt
            linuxhandbook:~$ chmod 4766 test2.txt
            linuxhandbook:~$ ls -l test2.txt
            -rwsrw-rw- 1 linuxhandbook linuxhandbook 0 Apr 12 17:54 test2.txt
            ```
        * How to remove SUID? -> `chmod u-s test.txt` or `chmod 0766 test2.txt` here `0` represent the remove permission

    * Difference between small s and capital S as SUID bit -> Remember the definition of SUID? It allows a file to be executed with the same permissions as the owner of the file. But what if the file doesn’t have execute bit set in the first place? Like this:
        `linuxhandbook:~$ ls -l test.txt`
        `-rw-rw-rw- 1 linuxhandbook linuxhandbook 0 Apr 12 17:51 test.txt`
        `chmod u+s test.txt`
        `ls -l test.txt`
        `-rwSrw-rw- 1 linuxhandbook linuxhandbook 0 Apr 12 17:52 test.txt`
        * The S as SUID flag means there is an error that you should look into. You want the file to be executed with the same permission as the owner but there is no executable permission on the file. Which means that not even the owner is allowed to execute the file and if file cannot be executed, you won’t get the permission as the owner. This fails the entire point of setting the SUID bit.
        * How to find all files with SUID set? ->  `find / -perm /4000`

* **SGID**
    * **What is SGID?** -> SGID is similar to SUID. With the SGID bit set, any user executing the file will have same permissions as the group owner of the file.
    * It’s benefit is in handling the directory. When SGID permission is applied to a directory, all sub directories and files created inside this directory will get the same group ownership as main directory (not the group ownership of the user that created the files and directories).
    * `d rwx rws r-x` -> This folder has the letter ‘s’ on the same place you expect to see ‘x’ or ‘-‘ for group permissions.
    * **How to set SGID?** -> `d rwx rwx r-x` -> `chmod g+s directory_name` -> `d rwx rws r-x` 
    * **The octal number used to SGID is always 2** -> `drw xrwx r-x` -> `chmod 2775 folder2` -> `d rwx rws r-x`
    * **How to remove SGID bit?** -> `chmod g-s folder` or `chmod 0755 folder`
    * **How to find files with SGID set in Linux** -> `find . -perm /2000`

* **Sticky Bit**
    * **What is a Sticky Bit?** -> The sticky bit works on the directory. With sticky bit set on a directory, all the files in the directory can only be deleted or renamed by the file owners only or the root.
    * `d rwx rwx rwt` -> the letter t on the same place we expect to see x or – for others permissions. This means that a user (except root) cannot delete the temporary files created by other users in the directory.
    * **How to set the sticky bit?** -> `d rwx rwx r-x` -> `chmod +t my_dir` -> `d rwx rwx r-t`
    * **The octal number used for sticky bit is always 1** -> `d rwx rwx r-x` -> `chmod 1775 my_dir/` -> `d rwx rwx r-t`
    * **How to remove the sticky bit:** -> `chmod -t my_dir` or `chmod 0775 my_dir`
    * **How to find files with sticky bit set in Linux** -> `find . -perm /1000`

* **que is what is difference between this two `chmod 0766 test2.txt` and `chmod 0755 folder` ?** -> 1st one for the File level and 2nd is for the Folder so, For the remeber purpose **file permission is SUID and folder level is SGID**
* **what is diff between `chmod 0775 folder/` and `chmod 0755 folder`** -> 
---


## 3. Linux Users and Groups Administration

*   **User Account Management**
    *   **User Types**: Regular users vs. System/Service accounts vs. Root (`UID 0`).
    *   **Core Files**:
        *   `/etc/passwd`: Stores user account records, UIDs, primary GIDs, shells, and home directory paths.
        *   `/etc/shadow`: Stores encrypted password hashes and account expiration policies securely.
*   **Group Management**
    *   Primary groups vs. Secondary/Supplemental groups.
    *   **Core Files**:
        *   `/etc/group`: Defines group definitions, GIDs, and group membership lists.
*   **Privilege Delegation (`sudo`)**
    *   Configuring security policies and administrative permissions via `/etc/sudoers` using `visudo`.

---

## Worked Examples

### Example 1: Fixing a Deployment Script Permission Denied Error
You push a shell script to a production server, but execution fails with a "Permission denied" error. You need to inspect and modify its permissions to allow the owner to execute it.

1. **Inspect current file permissions**: Run `ls -l deploy.sh` to check the current mode, owner, and group. Output shows `-rw-r--r--` (permissions: 644).
2. **Modify permissions using numeric mode**: Apply `chmod 755 deploy.sh` to grant read, write, and execute permissions to the owner, and read/execute to group and others.
3. **Verify execution rights**: Run `ls -l deploy.sh` again to confirm the mode reads `-rwxr-xr-x` (755), allowing safe execution.

### Example 2: Securing Sensitive Configuration Files
An application config file containing database credentials has permissions set too loosely (`-rw-rw-rw-`), exposing it to other system users.

1. **Check file ownership and permissions**: Run `ls -l /etc/app/config.json` and note that permissions are set to 666 (world-writable/readable).
2. **Restrict permissions to owner only**: Run `chmod 600 /etc/app/config.json` so only the owning service user can read and write the file.
3. **Verify owner assignment**: Ensure the correct system user owns the file using `chown appuser:appgroup /etc/app/config.json`.