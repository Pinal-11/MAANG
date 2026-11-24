# from pathlib import Path

# config_file = Path("app.log")
# backup_config_file = Path("config_backup.txt")
# try:
#     with config_file.open("r", encoding="utf-8") as file, backup_config_file.open("w", encoding="utf-8") as backup_output:
#         for line in file:
#             backup_output.write(line)
#         print("Backup is successfully completed")
# except FileNotFoundError:
#     print(f"{config_file} not found")

from pathlib import Path

config_file = Path("config.txt")
backup_config_file = Path("config_backup.txt")

try:
    with config_file.open("r", encoding="utf-8") as file, backup_config_file.open("w", encoding="utf-8") as backup_output:
        for line in file:
            backup_output.write(line)

except FileNotFoundError:
    print(f"ERROR: Source file {config_file} not found!")

except PermissionError:
    print("ERROR: Permission denied! Cannot access the file.")

except OSError as error:
    print(f"ERROR: File operation failed: {error}")

else:
    print("Backup completed successfully!")

finally:
    print("Backup operation finished.")