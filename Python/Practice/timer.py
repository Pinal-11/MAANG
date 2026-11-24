import time

# 1. Logging an event timestamp
print(f"Check started at Unix timestamp: {time.time()}")

# 2. Measuring latency/duration accurately
start = time.perf_counter()
time.sleep(0.5)  # Simulating an API call
elapsed = time.perf_counter() - start

print(f"Endpoint responded in {elapsed:.4f} seconds")
