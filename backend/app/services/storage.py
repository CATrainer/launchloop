import boto3
from botocore.config import Config
from typing import Optional
import mimetypes
from app.config import settings
from app.utils.helpers import generate_uuid


class StorageService:
    """Service for cloud storage (Cloudflare R2)"""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        self.bucket = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL
    
    def upload_image(
        self,
        image_data: bytes,
        filename: Optional[str] = None,
        content_type: str = "image/png"
    ) -> str:
        """
        Upload image to R2 and return public URL
        """
        # Generate unique filename if not provided
        if not filename:
            extension = mimetypes.guess_extension(content_type) or ".png"
            filename = f"images/{generate_uuid()}{extension}"
        
        # Upload to R2
        self.client.put_object(
            Bucket=self.bucket,
            Key=filename,
            Body=image_data,
            ContentType=content_type,
            CacheControl='public, max-age=31536000'
        )
        
        # Return public URL
        if self.public_url:
            return f"{self.public_url}/{filename}"
        else:
            # Fallback to R2 direct URL
            return f"https://{self.bucket}.{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{filename}"
    
    def upload_html(
        self,
        html_content: str,
        filename: str
    ) -> str:
        """Upload HTML file to R2"""
        
        self.client.put_object(
            Bucket=self.bucket,
            Key=filename,
            Body=html_content.encode('utf-8'),
            ContentType='text/html',
            CacheControl='public, max-age=3600'
        )
        
        if self.public_url:
            return f"{self.public_url}/{filename}"
        else:
            return f"https://{self.bucket}.{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{filename}"
    
    def delete_file(self, filename: str) -> bool:
        """Delete file from R2"""
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=filename
            )
            return True
        except Exception:
            return False


# Global service instance
storage_service = StorageService()
