import boto3
from botocore.exceptions import NoCredentialsError
from loguru import logger

from config import get_settings

logger = logger.bind(name="Utils")
settings = get_settings()

def generate_presigned_upload_url(user_id, filename, expiration=3600):
    """Generate a presigned URL for direct S3 upload."""
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION,
        )
        
        # Define the S3 key where the file will be uploaded
        s3_key = f"{user_id}/video/{filename}"
        
        # Generate presigned URL for PUT operation
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.BUCKET_NAME,
                'Key': s3_key,
                'ContentType': 'video/*'  # You can make this more specific based on file type
            },
            ExpiresIn=expiration  # URL expires in 1 hour by default
        )
        
        # Return both the presigned URL and the final S3 URL
        final_url = f"https://{settings.BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        
        logger.info(f"Generated presigned URL for {s3_key}")
        return {
            "presigned_url": presigned_url,
            "final_url": final_url,
            "s3_key": s3_key
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
    