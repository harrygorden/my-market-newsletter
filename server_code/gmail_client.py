#!/usr/bin/env python3
"""
gmail_client.py
Handles Gmail integration. This module retrieves the latest newsletter email from Gmail using the Gmail API.
It uses Anvil secrets for credentials/configuration to authenticate and fetch the email.
"""

import base64
import datetime
from email.utils import parsedate_to_datetime

import anvil.secrets
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


def find_body(payload):
    """Recursively search the payload for a body with data."""
    if 'body' in payload and 'data' in payload['body'] and payload['body']['data']:
        return base64.urlsafe_b64decode(payload['body']['data'].encode('UTF-8')).decode('UTF-8')
    if 'parts' in payload:
        for part in payload['parts']:
            result = find_body(part)
            if result:
                return result
    return None


def get_gmail_service():
    """
    Creates and returns an authenticated Gmail service using our OAuth credentials from Anvil secrets.
    """
    try:
        creds = Credentials(
            token=None,
            refresh_token=anvil.secrets.get_secret('google_refresh_token'),
            client_id=anvil.secrets.get_secret('google_client_id'),
            client_secret=anvil.secrets.get_secret('google_client_secret'),
            token_uri='https://oauth2.googleapis.com/token',
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        creds.refresh(Request())
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        print(f"Error creating Gmail service: {str(e)}")
        raise


def _get_latest_newsletter():
    """Synchronous helper function to retrieve the latest newsletter from Gmail."""
    try:
        print("Starting newsletter retrieval process")
        sender_email = anvil.secrets.get_secret('newsletter_sender_email')
        print(f"Looking for emails from: {sender_email}")

        service = get_gmail_service()

        # Search for the most recent email from the sender
        query = f"from:{sender_email}"
        results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()

        messages = results.get('messages', [])
        if not messages:
            print("No emails found from the specified sender")
            return None

        # Get the full email content
        msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)

        if not date_str:
            print("No date found in email.")
            return None

        try:
            news_timestamp = parsedate_to_datetime(date_str)
        except Exception as e:
            print("Error parsing date, using raw date:", e)
            news_timestamp = date_str

        body = find_body(msg['payload'])
        if body is None:
            print("Could not extract email body")
            return None

        # Return a dictionary consistent with our earlier design
        return {
            'received_date': news_timestamp.isoformat() if hasattr(news_timestamp, 'isoformat') else news_timestamp,
            'subject': subject,
            'raw_body': body
        }
    except Exception as e:
        print("Error retrieving newsletter: " + str(e))
        raise


def get_latest_newsletter():
    """
    Retrieves the latest newsletter email from Gmail.
    Returns a dictionary with keys: received_date, subject, and raw_body.
    """
    return _get_latest_newsletter() 