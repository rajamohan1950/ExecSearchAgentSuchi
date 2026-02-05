#!/usr/bin/env python3
"""
One-time script to generate Gmail OAuth2 token.json.

Usage:
    1. Download credentials.json from Google Cloud Console
    2. Place it in secrets/credentials.json
    3. Run: python services/outreach-agent/scripts/gmail_auth.py
    4. A browser will open for Google OAuth consent
    5. token.json will be saved to secrets/token.json

Scopes requested:
    - gmail.send: Send emails
    - gmail.readonly: Read inbox
    - gmail.modify: Manage labels/mark as read
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
secrets_dir = os.path.join(project_root, "secrets")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

credentials_path = os.path.join(secrets_dir, "credentials.json")
token_path = os.path.join(secrets_dir, "token.json")


def main():
    if not os.path.exists(credentials_path):
        print(f"ERROR: credentials.json not found at {credentials_path}")
        print("\nSteps:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Desktop Application)")
        print("3. Download the JSON file")
        print(f"4. Save it as {credentials_path}")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)

        os.makedirs(secrets_dir, exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

        print(f"\nToken saved to {token_path}")
        print("Gmail API is now configured for the outreach agent!")

    except ImportError:
        print("ERROR: google-auth-oauthlib not installed.")
        print("Run: pip install google-auth-oauthlib")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
