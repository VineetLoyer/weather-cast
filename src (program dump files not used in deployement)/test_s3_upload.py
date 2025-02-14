import boto3
import os
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def test_upload():
    """Test uploading a small file to S3"""
    file_content = "Hello, this is a test upload from WeatherCast!"
    file_name = "test_upload.txt"

    try:
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=file_name,
            Body=file_content
        )
        print(f"✅ Successfully uploaded {file_name} to {AWS_S3_BUCKET}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

if __name__ == "__main__":
    test_upload()
