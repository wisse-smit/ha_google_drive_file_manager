# get_drive_tokens.py
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# 1) Replace this client_config dict with your actual client ID/secret info.
#    You can also point to a client_secret.json downloaded from GCP if you prefer.
CLIENT_CONFIG = {
    "installed": {
        "client_id": os.getenv("GOOGLE_DRIVE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_DRIVE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080/"],  # or whatever you registered
    }
}

SCOPES = ["https://www.googleapis.com/auth/drive"]

def main():
    flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
    creds = flow.run_local_server(port=8080)  # opens a browser to your consent screen
    # creds.token is the access token, creds.refresh_token is long‐lived
    token_data = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "scopes": creds.scopes,
    }
    print(json.dumps(token_data, indent=2))

if __name__ == "__main__":
    main()
