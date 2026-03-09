import json
import os
from utils import encrypt, decrypt

BASE_DIR = os.path.join(os.getenv("APPDATA"), "TimeTracker")
CONFIG_FILE = os.path.join(BASE_DIR, "configs")

# App folder configurations
def get_config_file(user_email):
    os.makedirs(CONFIG_FILE, exist_ok=True)
    safe_email = user_email.replace("@", "_").replace(".", "_")
    return os.path.join(CONFIG_FILE, f"{safe_email}.json")

def load_config(user_email):
    path = get_config_file(user_email)

    if os.path.exists(path):
        with open(path, "rb") as f:
            encrypted = f.read()

        decrypted = decrypt(encrypted)        
        return json.loads(decrypted.decode())
    
    return {"clients": {}}

def save_config(user_email, data):
    path = get_config_file(user_email)

    raw = json.dumps(data).encode()
    encrypted = encrypt(raw)

    with open(path, "wb") as f:
        f.write(encrypted)