import re
import datetime
import os
import sys
from cryptography.fernet import Fernet

# Utilities or helpers for the core functionalities
# This file contains the extraction of the sheets url ID, Time stamp format, and the Encryption and Decryption of the data

KEY_FILE = os.path.join(os.getenv("APPDATA"), "TimeTracker", "key.key")

def extract_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def get_current_timestamp():
    now = datetime.datetime.now()
    return {
        'date': now.strftime("%Y-%m-%d"),
        'time': now.strftime("%H:%M:%S"),
        'datetime': now,
        'formatted_time': now.strftime('%I:%M %p')
    }

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# For Encryption
def get_key():
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)

    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()

    return key

def encrypt(data: bytes):
    f= Fernet(get_key())
    return f.encrypt(data)

def decrypt(data: bytes):
    f = Fernet(get_key())
    return f.decrypt(data)
    