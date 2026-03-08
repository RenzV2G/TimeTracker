import os
import gspread
import requests as http_requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import id_token
from google.auth.transport import requests

from constants import SCOPES

TOKEN_FILE = "data/tokens"
CLIENT_SECRET_FILE = "client_secret.json"

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
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

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

                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())

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
