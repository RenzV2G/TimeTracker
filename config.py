import json
import os

CONFIG_FILE = "data/configs"

def get_config_file(user_email):
    os.makedirs(CONFIG_FILE, exist_ok=True)
    safe_email = user_email.replace("@", "_").replace(".", "_")
    return os.path.join(CONFIG_FILE, f"{safe_email}.json")

def load_config(user_email):
    path = get_config_file(user_email)

    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
        
    return {"clients": {}}

def save_config(user_email, data):
    path = get_config_file(user_email)

    with open(path, "w") as f:
        json.dump(data, f, indent=4)