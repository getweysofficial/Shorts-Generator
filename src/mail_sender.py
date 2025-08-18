import os
import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from loguru import logger

logger = logger.bind(name="Mail Sender")

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    """Authenticate and return Gmail service."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def send_email(to,shorts_path, sender="me"):
    """Send an email with Gmail API."""
    service = get_gmail_service()

    subject = "Your Shorts Are Ready 🎬"
    body = "Hello!\n\nYour video shorts are ready.\nYou can find them here:\n{}\n\nCheers!".format(shorts_path)

    message = MIMEText(body)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message = {"raw": raw_message}

    sent = service.users().messages().send(userId="me", body=message).execute()
    logger.info(f"Email sent to {to} (Message ID: {sent['id']})")
    return sent


