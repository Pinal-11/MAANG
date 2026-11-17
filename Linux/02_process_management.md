jobs: will show active jobs
bg: Resume Job to the background
fg: Resume job to the foreground

How to run the specific jobs in the fg/bg
fg/bg %<Jobs Id>

## nice
niceness scale goes from -20 to 19 and the lower value gets more priority.
process priority = nice
ex - nice -n 5 process
     nice -n -10 /home/pinal/echo.sh

`ps -ef` to check the process info
`ps -l pid` to check the process info like nice value and all stuff.

## nohup
If you want your process keep running even after closing your terminal, you can use nohup.

nohup process &
nohup process >/dev/null 2>&1 &

## ps process status
This command used to display all running process in the linux system.

`ps` command show the process of current shell
```bash
Pinals-MacBook-Air:~ root# ps 
PID    TTY        TIME     CMD
55765 ttys005    0:00.02  login -pf pinaldadhania
55774 ttys005    0:00.03  sudo -i
55775 ttys005    0:00.02  -sh
56932 ttys005    0:00.01  ps
```

`PID` -> Unique process Id
`TTY` -> Terminal types of used loggedIn to
`TIME` -> amount of CPU in min and sec that process has been running
`CMD` -> name of the command which launch the process

`ps -e` or `ps -A` -> To see all the running processes across the system
`ps -ef` list the process but in the full format
`ps -ef | more` to view line by line like from top to bottom use `more` command
`ps aux` -> it gives you more info about the BSD format (Berkeley Software Distribution)
`ps -u <username>` to see the process by username
`ps -G <groupname>` to see the process by Group Name

---

## kill -> used to terminate a process manually 
Syntax:
` kill [Options] [PID]`
` Options -> singnal name or number`
` PID -> process Id`

`kill -l` -> to see all the signal name

widley used command

```bash
kill PID        # To kill the process -> zsh: terminated  sleep 50s
kill -1 PID     # To restart Process 
kill -2 PID     # To interrupt from keyboard like ctrl+c -> nothing because it is same as the ctrl+c in the terminal
kill -9 PID     # Forcefully terminate the process -> killed
kill -15 PID    # Kill process gracefully but in the status will show the terminated
```
---
# systemctl
What is Systemctl -> It is used to control the status of the services.
Control systemd system
```bash
sudo su
systemctl is_enabled <service_name> # To check service is enabled or not, The command will return enable/disable value 
systemctl enable --now <service_name> # to enable and start the service in one command

systemctl disable <service_name> 

systemctl mask <service_name>   # To prevent service from start

systemctl status <service_name>
systemctl stop <service_name>
systemctl start <service_name>
systemctl restart <service_name>

```
So the thing is: if the service us mask then we will not directly start the service first need to unmask the service then we can start but now i have another que is if service is disabled and mask then we will directly not start first need to unmask it and then start or do we need to enabled the service but and what is the use case of it behind the disabled and enbled the service ?? 
Oky so enable/disable will use to not to start when the system is reboot

# Control Command
```bash
systemctl poweroff
systemctl reboot
systemctl -i reboot # Ignoring the logged-in user
```

# IPC Inter Process Communication Command
To list the socket in memory available for

```bash
systemctl list-sockets
systemctl --show-type list-sockets
systemctl --show-type list-sockets 'systemd*'
systemctl --show-type list-sockets --all
```
---

## TOP (Table Of Process)
The `top` command shows a real-time view of running process in linux and display kernel-managed tasks.
The command also provides a system informations summary that shows resource utilization, including CPU and Memory usage.
there are so many flag we can use in the TOP command

---

## Cron Job
what is a cron job -> A cron job is a scheduled task that allows you to run scripts or commands at specified intervals
why used Cron Jobs -> Cron Job automate the repetative task, ensuring they run at scheduled times without manual intervention.
example -> Backing up files, running system maintenance, or sending email reports
How it works -> Cron uses a `daemon (background process) called cron` to execute schedule tasks.
-> The Configuration for these tasks is stored in a file called a  `crontab`
-> Name of the service is: `Crond`

### Crontab
* command to edit crontab -> `crontab -e`
* How to view your current cron Jobs -> `crontab -l`
* Deleting cron jobs with `crontab -r` (warning: It will remove all the jobs)

```bash
crontab -e # to edit the crontab
# now we are in the crontab
# here we can define the our multiple cronjobs that we want to schedule
# press i for the insert for this crontab is the same as the vi file editor 

30 14 * * 0 /tmp/basic.sh
* * * * *  <script location>

```

* * * * * 
| | | | |__week days (0 - 6) 0->sun 
| | | |____ month (1 - 12)
| | |_______day (1 - 31) month day
| |__________Hour (0 - 23)
|_____________ minutes (0 - 59)

-----

```bash
0 0 * * * (12 midnight daily)
30 8 1 * * (1st of every month, at 8:30 AM)
*/15 * * * * (every 15 min)
15 14 * * 1-5 (2:15 PM Monday - Friday)
0 20 10,20,30 2 * (February, 8 PM on 10th, 20th 30th on any day)

```

Special Characters:
(*) -> Represents all possible value for a field. For example, using an * in the month field means every month
(,) -> Allows you to specify multiple values in a fiels. For example, Mon, Wed, Fri in the dayy of the week field means Mondays, Weds, Fridays
(-) -> 