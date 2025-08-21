import boto3
from botocore.exceptions import NoCredentialsError
from loguru import logger

from config import get_settings

logger = logger.bind(name="Utils")
settings = get_settings()

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
        print("AWS credentials not available.")
