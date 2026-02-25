import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import gspread
from constants import SCOPES

TOKEN_FILE = "token.json"
CLIENT_SECRET_FILE = "client_secret.json"

class GoogleAuth:
    
    @staticmethod
    def is_logged_in():
        return os.path.exists(TOKEN_FILE)
    
    @staticmethod
    def authenticate():
        creds = None
        
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        
        return gspread.authorize(creds)
    
    @staticmethod
    def sign_out():
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)