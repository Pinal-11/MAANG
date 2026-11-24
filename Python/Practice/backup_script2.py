from pathlib import Path

config_file = Path("error.log")
backup_config_file = Path("config_backup.txt")

try:
    # Check whether the source file exists
    if not config_file.exists():
        raise FileNotFoundError("Configuration file not found!")

    # Check whether the source file is empty
    size = config_file.stat().st_size
    print("Size: ", size)

    if size == 0:
        raise ValueError("Configuration file is empty!")

    # Read source file and create backup
    with config_file.open("r", encoding="utf-8") as file, \
         backup_config_file.open("w", encoding="utf-8") as backup_output:

        for line in file:
            backup_output.write(line)

except FileNotFoundError as error:
    print(f"ERROR: {error}")

except ValueError as error:
    print(f"ERROR: {error}")

except PermissionError:
    print("ERROR: Permission denied!")

except OSError as error:
    print(f"File operation failed: {error}")

else:
    print("Backup completed successfully!")

finally:
    print("Configuration validation finished.")