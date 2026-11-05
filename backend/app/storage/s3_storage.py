import os
import uuid
import boto3
from botocore.exceptions import ClientError
from backend.app.storage.base import BaseStorageProvider
from backend.app.core.config import settings

class S3StorageProvider(BaseStorageProvider):
    def __init__(self):
        client_kwargs = {
            "region_name": settings.AWS_REGION
        }
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        self.s3_client = boto3.client("s3", **client_kwargs)
        self.bucket = settings.AWS_S3_BUCKET

    def save_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        safe_name = os.path.basename(filename).replace(" ", "_")
        key = f"documents/{uuid.uuid4().hex[:12]}_{safe_name}"
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
            ServerSideEncryption="AES256"
        )
        return key

    def get_file_bytes(self, storage_key: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket, Key=storage_key)
        return response["Body"].read()

    def get_download_url(self, storage_key: str, expires_in: int = 3600) -> str:
        url = self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": storage_key},
            ExpiresIn=expires_in
        )
        return url

    def delete_file(self, storage_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=storage_key)
            return True
        except ClientError:
            return False
