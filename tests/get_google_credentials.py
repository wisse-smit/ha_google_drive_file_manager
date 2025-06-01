# test_drive_list.py

import os
from dotenv import load_dotenv
from pathlib import Path

from google.oauth2.credentials import Credentials

def get_google_drive_credentials():
    # We want to point load_dotenv() at the repo root’s .env, so:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)

    # Now os.getenv(...) can read from .env:
    CLIENT_ID = os.getenv("GOOGLE_DRIVE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET")
    ACCESS_TOKEN = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN")
    REFRESH_TOKEN = os.getenv("GOOGLE_DRIVE_REFRESH_TOKEN")

    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        raise RuntimeError("Please set GOOGLE_DRIVE_CLIENT_ID, GOOGLE_DRIVE_CLIENT_SECRET, and GOOGLE_DRIVE_REFRESH_TOKEN in your .env")

    OAUTH2_TOKEN_URI = "https://oauth2.googleapis.com/token"
    SCOPES = ["https://www.googleapis.com/auth/drive"]  # or ["https://www.googleapis.com/auth/drive"] for full access

    # Gets the credentials using the provided tokens, if expired, the library will handle refreshing them automatically
    credentials = Credentials(
        token=ACCESS_TOKEN,
        refresh_token=REFRESH_TOKEN,
        token_uri=OAUTH2_TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
    )

    return credentials