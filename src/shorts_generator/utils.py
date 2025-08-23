import boto3
import mimetypes
import re
from datetime import datetime
from botocore.exceptions import NoCredentialsError
from loguru import logger

from config import get_settings

logger = logger.bind(name="Utils")
settings = get_settings()

def sanitize_filename(filename):
    """Convert filename to proper format: abc-xyz-timestamp.extension"""
    # Remove file extension
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    
    # Replace spaces and special characters with hyphens
    sanitized_name = re.sub(r'[^a-zA-Z0-9]', '-', name)
    # Remove multiple consecutive hyphens
    sanitized_name = re.sub(r'-+', '-', sanitized_name)
    # Remove leading/trailing hyphens
    sanitized_name = sanitized_name.strip('-')
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Reconstruct filename
    if ext:
        return f"{sanitized_name}-{timestamp}.{ext.lower()}"
    else:
        return f"{sanitized_name}-{timestamp}"

def get_content_type(filename):
    """Get proper content type based on file extension"""
    # Get MIME type from filename
    content_type, _ = mimetypes.guess_type(filename)
    
    # Map common video extensions to proper MIME types
    video_extensions = {
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.webm': 'video/webm',
        '.m4v': 'video/x-m4v',
        '.3gp': 'video/3gpp',
        '.ogv': 'video/ogg'
    }
    
    # Check if it's a video file
    for ext, mime_type in video_extensions.items():
        if filename.lower().endswith(ext):
            return mime_type
    
    # If not a video file, return the guessed type or default
    return content_type or 'application/octet-stream'

def generate_presigned_upload_url(user_id, filename, expiration=3600):
    """Generate a presigned URL for direct S3 upload."""
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION,
        )
        
        # Sanitize filename and get content type
        sanitized_filename = sanitize_filename(filename)
        content_type = get_content_type(filename)
        
        # Define the S3 key where the file will be uploaded
        s3_key = f"{user_id}/video/{sanitized_filename}"
        print(s3_key)
        print(content_type)
        print(sanitized_filename)
        
        # Generate presigned URL for PUT operation
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.BUCKET_NAME,
                'Key': s3_key,
                'ContentType': 'video/*'  
            },
            ExpiresIn=expiration  # URL expires in 1 hour by default
        )
        print(presigned_url)
        
        # Return both the presigned URL and the final S3 URL
        final_url = f"https://{settings.BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        
        logger.info(f"Generated presigned URL for {s3_key} with content type: {content_type}")
        return {
            "presigned_url": presigned_url,
            "final_url": final_url,
            "s3_key": s3_key,
            "sanitized_filename": sanitized_filename,
            "content_type": content_type
        }
        
    except NoCredentialsError:
        logger.error("AWS credentials not available.")
        raise
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise

def upload_to_s3(file_paths,user_id,task_id=None,filename=None,file_upload=False):
    """Upload a file to an S3 bucket."""

    uploaded_shorts = []

    try:
          s3_client = boto3.client(
               "s3",
               aws_access_key_id=settings.AWS_ACCESS_KEY,
               aws_secret_access_key=settings.AWS_SECRET_KEY,
               region_name=settings.AWS_REGION,
          )

          if file_upload:
           
            s3_path = f"{user_id}/video/{filename}"
            s3_client.upload_fileobj(file_paths, settings.BUCKET_NAME, s3_path) 
            logger.info(f"Upload successful! s3://{settings.BUCKET_NAME}/{s3_path}")
            uploaded_shorts=f"https://{settings.BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_path}"

            return uploaded_shorts

          else:
            for i,paths in enumerate(file_paths):
                    s3_path = f"{user_id}/{task_id}/shorts/short{i+1}.mp4"
                    s3_client.upload_file(paths, settings.BUCKET_NAME, s3_path)
                    logger.info(f"Upload successful! s3://{settings.BUCKET_NAME}/{s3_path}")
                    uploaded_shorts.append(f"https://{settings.BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_path}")
            
            return uploaded_shorts
    

    except FileNotFoundError:
        logger.info(("File not found."))

    except NoCredentialsError:
        logger.info("AWS credentials not available.")


def retrieve_from_s3(user_id,task_id):
    """Retrieve Shorts of specific video from s3"""

    shorts = {}
    bucket_name = settings.BUCKET_NAME
    folder_prefix = f"{user_id}/{task_id}/shorts/"

    try:
        s3_client = boto3.client(
               "s3",
               aws_access_key_id=settings.AWS_ACCESS_KEY,
               aws_secret_access_key=settings.AWS_SECRET_KEY,
               region_name=settings.AWS_REGION,
          )
        
        response = s3_client.list_objects_v2(Bucket=bucket_name,Prefix=folder_prefix)

        if 'Contents' in response:
            no_of_shorts = len(response["Contents"])
            for index in range(no_of_shorts):
                shorts[f"short_{index+1}"] = f"https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{user_id}/{task_id}/shorts/short{index+1}.mp4"
        else:
            logger.info(f"No objects found in folder: {folder_prefix}")

        return shorts
    except NoCredentialsError:
        logger.info("AWS credentials not available.")
    