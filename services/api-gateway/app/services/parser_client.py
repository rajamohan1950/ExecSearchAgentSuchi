import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PARSER_TIMEOUT = 30.0  # seconds
MAX_RETRIES = 3


async def parse_linkedin_pdf(pdf_bytes: bytes, filename: str) -> dict:
    url = f"{settings.parser_service_url}/parse/linkedin-pdf"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=PARSER_TIMEOUT) as client:
                files = {"file": (filename, pdf_bytes, "application/pdf")}
                response = await client.post(url, files=files)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Parser returned {e.response.status_code}: {e.response.text}")
            raise
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(f"Parser connection attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES:
                raise
            continue
