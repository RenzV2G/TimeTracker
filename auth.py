import os
import gspread
import requests as http_requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from utils import encrypt, decrypt, resource_path
import json
import uuid

from constants import SCOPES

# Authentication for the googleAuth, this requires more security to prevent vulnerabilities to the application.


DEVICE_ID = hex(uuid.getnode())
BASE_DIR = os.path.join(os.getenv("APPDATA"), "TimeTracker")
TOKEN_FILE = os.path.join(BASE_DIR, "tokens")
CLIENT_SECRET_FILE = resource_path("client_secret.json")


def safe_email(email):
    return email.replace("@", "_").replace(".", "_")

class GoogleAuth:

    def __init__(self):
        os.makedirs(TOKEN_FILE, exist_ok=True)
        self.user_email = None
        self.token_file = None
        self.creds = None

    def get_token_path(self, email):
        return os.path.join(TOKEN_FILE, f"{safe_email(email)}_token.json")
    
    def is_logged_in(self):
        if not os.path.exists(TOKEN_FILE):
            return False
        
        tokens = [f for f in os.listdir(TOKEN_FILE) if f.endswith("_token.json")]

        if not tokens:
            return False

        # Load first token automatically
        token_path = os.path.join(TOKEN_FILE, tokens[0])
        self.token_file = token_path

        # extract email from filename
        email = tokens[0].replace("_token.json", "")
        self.user_email = email.replace("_", "@", 1).replace("_", ".")

        return True
    
    def authenticate(self):
        creds = None
        
        if self.token_file and os.path.exists(self.token_file):
            with open(self.token_file, "rb") as f:
                encrypted = f.read()
            
            decrypted = decrypt(encrypted).decode()
            data = json.loads(decrypted)

            if data.get("device_id") != DEVICE_ID:
                raise Exception("Token belongs to another device.")
            creds = Credentials.from_authorized_user_info(data, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    raise Exception("Session expired. Please sign in again.")

            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES
                )

                creds = flow.run_local_server(port=0)

                response = http_requests.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {creds.token}"}
                )

                info = response.json()

                email = info.get("email")

                if not email:
                    raise Exception("Could not retrieve Google Account Email.")

                self.user_email = email
                self.token_file = self.get_token_path(self.user_email)

                data = json.loads(creds.to_json())
                data["device_id"] = DEVICE_ID

                encrypted = encrypt(json.dumps(data).encode())

                with open(self.token_file, "wb") as token:
                    token.write(encrypted)

        # Get Email if not set yet
        if not self.user_email:
            response = http_requests.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {creds.token}"}
                )

            info = response.json()

            email = info.get("email")

            if not email:
                raise Exception("Could not retrieve Google Account Email.")

            self.user_email = email
            self.token_file = self.get_token_path(self.user_email)
        
        self.creds = creds

        return gspread.authorize(creds)
    
    def sign_out(self):
        if self.token_file and os.path.exists(self.token_file):
            os.remove(self.token_file)

        self.user_email = None
        self.creds = None
        self.token_file = None
