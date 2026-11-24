
from pathlib import Path
import logging

log_file = Path("app.log")
error_file = Path("errors.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

counts = {
    "INFO": 0,
    "WARNING": 0,
    "ERROR": 0
}

total_lines = 0

try:
    with log_file.open("r", encoding="utf-8") as file, error_file.open("w", encoding="utf-8") as output:
        for line in file:
            total_lines += 1

            parts = line.split(maxsplit=3)

            if len(parts) < 3:
                continue

            level = parts[2]

            if level in counts:
                counts[level] += 1

                if level == "ERROR":
                    output.write(line)

    logging.info("Total lines processed: %d", total_lines)

    for level, count in counts.items():
        logging.info("%s: %d", level, count)

    logging.info(
        "Extracted %d errors to %s",
        counts["ERROR"],
        error_file
    )

except FileNotFoundError:
    logging.error("Log file not found: %s", log_file)

except PermissionError:
    logging.error("Permission denied while accessing files")

except OSError as e:
    logging.exception("File processing failed: %s", e)
