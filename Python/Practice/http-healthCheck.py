import requests
import time

# The requests library allows Python to communicate with HTTP/HTTPS endpoints.
# For example, it can send GET and POST requests to APIs.

urls = ["https://google.com","https://github.com","https://examples.com","https://nonexistent-domain-12345.com"]

# store multiple URLs in a Python list. because want to check multiple application endpoints instead of writing separate code for every URL.
healthy_count = 0
unhealthy_count = 0
total_response_time = 0

for url in urls:
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()

        response_time = end_time - start_time

        if response.status_code == 200:
            print(f"{url} - Healthy - Response Time: {response_time:.2f} seconds")
            healthy_count += 1
            total_response_time += response_time

        else:
            print(f"{url} - UnHealthy (Status : {response.status_code}) - Response Time: {response_time:.2f} seconds")
            unhealthy_count += 1
    
    except requests.exceptions.Timeout:
        print(f"{url} : TIMEOUT")
        unhealthy_count += 1

    except requests.exceptions.ConnectionError:
        print(f"{url} : Connection Error")
        unhealthy_count += 1

    except requests.exceptions.RequestException as error:
        print(f"{url} - ERROR : {error} ")
        unhealthy_count += 1

total = healthy_count + unhealthy_count
print("========== SUMMARY ==========")
print(f"Total endpoints : {total}")
print(f"Healthy endpoints: {healthy_count}")
print(f"Unhealthy endpoints: {unhealthy_count}")

if healthy_count > 0:
    average_response_time = total_response_time / healthy_count
    print(f"Average Respose Time : {average_response_time:.2f} seconds")
else:
    print("Average response time: Not available (No healthy endpoints)")