from collections import Counter
from pathlib import Path

log_file = Path("app.log")
error_file = Path("error.log")

level_counts = Counter({"INFO": 0, "WARNING": 0, "ERROR": 0})
error_messages = Counter()
total_entries = 0

with log_file.open("r", encoding="utf-8") as file, error_file.open("w", encoding="utf-8") as error_output:
    for line in file:
        for level in level_counts:
            if level in line:
                level_counts[level] += 1
                total_entries += 1

                if level == "ERROR":
                    error_output.write(line)
                    # Strip whitespace/newlines so identical errors group together cleanly
                    error_messages[line.strip()] += 1
                break

print("========== LOG ANALYSIS REPORT ==========")
print(f"Total log entries: {total_entries}")

for level, count in level_counts.items():
    print(f"{level}: {count}")

print("\nMost frequent error:")
if error_messages:
    top_error, freq = error_messages.most_common(1)[0]
    print(f"({freq}x) {top_error}")
else:
    print("None")

print(f"\nExtracted {level_counts['ERROR']} errors to {error_file.name}")
