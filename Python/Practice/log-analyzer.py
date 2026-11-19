from pathlib import Path 

log_file = Path("app.log")
error_file = Path("error.log")

counts = {"INFO":0, "WARNING":0, "ERROR":0 }

with log_file.open("r", encoding="utf-8") as file, error_file.open("w", encoding="utf-8") as error_output:
    for line in file:
        for level in counts:
            if level in line:
                counts[level] += 1

                if level == "ERROR":
                    error_output.write(line)
                
                break

print("Log Analysis Report")
print("-------------------")

for level, count in counts.items():
    print(f"{level}: {count}")

print(f"\nExtracted {counts['ERROR']} errors to errors.log")
