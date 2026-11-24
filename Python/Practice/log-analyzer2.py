from pathlib import Path
from collections import Counter

log_file = Path("app.log")
error_file = Path("error.log")

counts = {
    "INFO": 0,
    "WARNING": 0,
    "ERROR": 0
}

error_counts = Counter()
total_logs = 0

try:
    with log_file.open("r", encoding="utf-8") as file, error_file.open("w", encoding="utf-8") as error_output:
        for line in file:
            line = line.strip()

            if not line:
                continue

            total_logs += 1

            if "INFO" in line or "Info" in line:
                counts["INFO"] += 1

            elif "WARNING" in line or "Warning" in line:
                counts["WARNING"] += 1

            elif "ERROR" in line or "Error" in line:
                counts["ERROR"] += 1

                error_message = line.replace("ERROR ", "", 1)

                error_counts[error_message] += 1

                error_output.write(line + "\n")

    print("========== LOG ANALYSIS REPORT ==========")

    print(f"\nTotal log entries: {total_logs}")

    for level, count in counts.items():
        print(f"{level}: {count}")

    print("\nMost frequent error:")

    if error_counts:
        for message, count in error_counts.most_common(3):
            print(f"{message} - {count} times")
    else:
        print("No errors found.")

    print("\nError log generated: error.log")

except FileNotFoundError:
    print("Error: Application log file not found!")

except OSError as error:
    print(f"File operation failed: {error}")