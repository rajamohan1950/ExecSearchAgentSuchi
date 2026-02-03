import logging

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.storage_endpoint,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            config=BotoConfig(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self.bucket = settings.storage_bucket

    def ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            logger.info(f"Creating bucket: {self.bucket}")
            self.client.create_bucket(Bucket=self.bucket)

    def upload_pdf(self, user_id: str, version: int, file_bytes: bytes, filename: str) -> str:
        key = f"profiles/{user_id}/v{version}/{filename}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_bytes,
            ContentType="application/pdf",
        )
        logger.info(f"Uploaded PDF: {key}")
        return key

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )


storage_service = StorageService()
