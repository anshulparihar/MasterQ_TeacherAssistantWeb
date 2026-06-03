import boto3
from botocore.exceptions import ClientError
import structlog
from app.config import settings

logger = structlog.get_logger()

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}" if not settings.MINIO_ENDPOINT.startswith("http") else settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name='us-east-1' # Default for minio
        )

    def upload_file(self, bucket: str, key: str, file_bytes: bytes, content_type: str) -> str:
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_bytes,
                ContentType=content_type
            )
            return f"{bucket}/{key}"
        except ClientError as e:
            logger.error("Failed to upload file to MinIO", error=str(e))
            raise

    def download_file(self, bucket: str, key: str) -> bytes:
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            logger.error("Failed to download file from MinIO", error=str(e))
            raise

    def delete_file(self, bucket: str, key: str) -> None:
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
        except ClientError as e:
            logger.error("Failed to delete file from MinIO", error=str(e))
            raise

    def generate_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires
            )
            return url
        except ClientError as e:
            logger.error("Failed to generate presigned URL", error=str(e))
            raise

storage_service = StorageService()
