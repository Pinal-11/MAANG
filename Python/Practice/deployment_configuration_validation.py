"""
Write a script that:
1. Checks whether deployment.yaml exists.
2. If missing, raises FileNotFoundError.
3. Checks whether the file is empty. If empty, raises ValueError.
4. Checks whether the file contains the word kind: Deployment. If not, raises ValueError with the message "Invalid Kubernetes deployment configuration".
5. If all validations pass, print "Deployment configuration is valid!".
6. Handle the exceptions separately.
7. Use finally to print "Validation process completed.".

"""

from pathlib import Path

config_file = Path("deployment.yaml")

try:
    if not config_file.exists():
        raise FileNotFoundError("Deployment file is not Found")
    
    size = config_file.stat().st_size

    if size == 0:
        raise ValueError("Deployment file is empty")

    with config_file.open("r", encoding="utf-8") as file:
        # content = file.read() 
    
        if "kind: Deployment" not in file.read():
            raise ValueError("Invalid Kubernetes deployment configuration") 
            
except FileNotFoundError as error:
    print("ERROR:", error)

except ValueError as error:
    print("ERROR:", error)

except PermissionError as error:
    print("ERROR:", error)

except OSError as error:
    print("ERROR:", error)

else:
    print("Deployment configuration is valid!")  

finally:
    print("Validation process completed.")



