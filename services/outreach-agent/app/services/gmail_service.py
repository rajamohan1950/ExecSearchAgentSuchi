"""Gmail API integration for sending and receiving emails."""

import base64
import logging
import os
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailService:
    """Wrapper around Gmail API for sending/receiving emails."""

    def __init__(self):
        self._service = None
        self._initialized = False

    def _get_service(self):
        """Build Gmail API service using OAuth2 credentials (lazy init)."""
        if self._service and self._initialized:
            return self._service

        creds = None
        token_path = settings.gmail_token_json
        creds_path = settings.gmail_credentials_json

        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load token.json: {e}")

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
                logger.info("Gmail token refreshed")
            except Exception as e:
                logger.error(f"Failed to refresh Gmail token: {e}")
                creds = None

        if not creds or not creds.valid:
            if os.path.exists(creds_path):
                logger.warning(
                    "Gmail credentials not valid. Run scripts/gmail_auth.py to generate token.json"
                )
            else:
                logger.warning("Gmail credentials.json not found. Email features disabled.")
            return None

        self._service = build("gmail", "v1", credentials=creds)
        self._initialized = True
        logger.info("Gmail API service initialized")
        return self._service

    async def send_email(
        self,
        to: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Send an email via Gmail API.

        Returns: {"message_id": str, "thread_id": str} or None on failure.
        """
        service = self._get_service()
        if not service:
            logger.error("Gmail service not available — cannot send email")
            return None

        try:
            msg = MIMEMultipart("alternative")
            msg["To"] = to
            msg["From"] = f"{settings.gmail_sender_name} <{settings.gmail_sender_email}>"
            msg["Subject"] = subject

            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
                msg["References"] = in_reply_to

            msg.attach(MIMEText(body_text, "plain"))
            if body_html:
                msg.attach(MIMEText(body_html, "html"))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            send_body = {"raw": raw}
            if thread_id:
                send_body["threadId"] = thread_id

            result = (
                service.users()
                .messages()
                .send(userId="me", body=send_body)
                .execute()
            )

            logger.info(f"Email sent to {to} — message_id={result.get('id')}, thread_id={result.get('threadId')}")
            return {
                "message_id": result.get("id"),
                "thread_id": result.get("threadId"),
            }

        except HttpError as e:
            logger.error(f"Gmail API error sending to {to}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return None

    async def get_new_messages(self, since_timestamp: datetime) -> list[dict]:
        """
        Fetch messages received after a given timestamp.

        Returns list of:
        {
            "message_id": str,
            "thread_id": str,
            "from_email": str,
            "subject": str,
            "body_text": str,
            "received_at": datetime,
        }
        """
        service = self._get_service()
        if not service:
            return []

        try:
            # Gmail API query: after:epoch_seconds
            epoch = int(since_timestamp.timestamp())
            query = f"after:{epoch} is:inbox"

            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=50)
                .execute()
            )

            messages_meta = results.get("messages", [])
            if not messages_meta:
                return []

            parsed_messages = []
            for msg_meta in messages_meta:
                try:
                    msg = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_meta["id"], format="full")
                        .execute()
                    )
                    parsed = self._parse_message(msg)
                    if parsed:
                        parsed_messages.append(parsed)
                except Exception as e:
                    logger.warning(f"Failed to fetch message {msg_meta['id']}: {e}")

            return parsed_messages

        except HttpError as e:
            logger.error(f"Gmail API error fetching messages: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch messages: {e}")
            return []

    async def get_thread_messages(self, thread_id: str) -> list[dict]:
        """Get all messages in a Gmail thread."""
        service = self._get_service()
        if not service:
            return []

        try:
            thread = (
                service.users()
                .threads()
                .get(userId="me", id=thread_id, format="full")
                .execute()
            )

            messages = []
            for msg in thread.get("messages", []):
                parsed = self._parse_message(msg)
                if parsed:
                    messages.append(parsed)

            return messages

        except Exception as e:
            logger.error(f"Failed to fetch thread {thread_id}: {e}")
            return []

    def _parse_message(self, msg: dict) -> Optional[dict]:
        """Parse a Gmail API message into a clean dict."""
        try:
            headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}

            from_email = headers.get("from", "")
            # Extract email from "Name <email>" format
            if "<" in from_email and ">" in from_email:
                from_email = from_email.split("<")[1].rstrip(">")

            body_text = self._extract_body(msg["payload"])
            internal_date = int(msg.get("internalDate", 0)) / 1000

            return {
                "message_id": msg["id"],
                "thread_id": msg.get("threadId"),
                "from_email": from_email.strip(),
                "to_email": headers.get("to", ""),
                "subject": headers.get("subject", ""),
                "body_text": body_text,
                "received_at": datetime.fromtimestamp(internal_date, tz=timezone.utc),
                "gmail_message_id": headers.get("message-id", ""),
            }
        except Exception as e:
            logger.warning(f"Failed to parse message: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain text body from message payload."""
        if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        for part in payload.get("parts", []):
            text = self._extract_body(part)
            if text:
                return text

        return ""


# Singleton instance
gmail_service = GmailService()
