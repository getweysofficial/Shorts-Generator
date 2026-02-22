"""
Modal deployment for Shorts Generator

This file replaces the Celery/Redis architecture with Modal functions.
The FastAPI app runs as a Modal web endpoint, and background tasks
are handled by Modal functions.
"""

import os
import shutil
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import modal

# Initialize Modal app
app = modal.App("shorts-generator")

# Define the image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install(
        "ffmpeg",
        "libsm6",
        "libxext6",
        "libxrender-dev",
        "libgomp1",
    )
    .pip_install(
        "boto3>=1.40.11",
        "click>=8.2.1",
        "email-validator>=2.0.0",
        "fastapi>=0.116.1",
        "google_auth_oauthlib>=1.2.2",
        "google-api-python-client>=2.179.0",
        "google-genai>=1.26.0",
        "groq>=0.30.0",
        "loguru>=0.7.3",
        "moviepy>=2.2.1",
        "pydantic>=2.11.7",
        "pydantic-settings>=2.10.1",
        "python-multipart>=0.0.6",
        "requests>=2.31.0",
        "scipy>=1.16.0",
        "uvicorn>=0.35.0",
    )
    .add_local_dir("./src", "/root/src")
)

# Create a shared volume for temporary file storage
volume = modal.Volume.from_name("shorts-generator-storage", create_if_missing=True)

# Secret for environment variables
secrets = [modal.Secret.from_name("custom-secret")]

base_path = "/tmp/data"


def send_webhook_notification(user_id, task_id, shorts_data, user_email, video_url, shorts_time, transcriptions, short_transcriptions):
    """Send webhook notification to external endpoint with all shorts data."""
    from config import get_settings
    from loguru import logger
    
    settings = get_settings()
    logger = logger.bind(name="ModalTask")
    
    try:
        webhook_url = "https://aknmrvakxkffztnlfmzr.supabase.co/functions/v1/video-completion-webhook"
        
        payload = {
            "user_id": user_id,
            "task_id": task_id,
            "user_email": user_email,
            "video_url": video_url,
            "shorts_time": shorts_time,
            "shorts": shorts_data,
            "transcriptions": transcriptions,
            "short_transcriptions": short_transcriptions,
            "status": "completed",
            "timestamp": str(datetime.now().isoformat())
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Webhook notification sent successfully to {webhook_url}")
        else:
            logger.warning(f"Webhook notification failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.error(f"Failed to send webhook notification: {e}")


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=3600,  # 1 hour timeout for long video processing
    cpu=4,  # Adjust based on your needs
    memory=8192,  # 8GB RAM
)
def generate_shorts_task(user_id: str, user_email: str, video_url: str, shorts_time: int, task_id: str):
    """
    Modal function that replaces the Celery task.
    Processes video and generates shorts.
    """
    import sys
    sys.path.insert(0, "/root/src")
    
    from loguru import logger
    from shorts_generator.video_processor import VideoProcessor
    from shorts_generator.audio_trancriber import AudioTranscriber
    from shorts_generator.shorts_agent import ShortsAgent
    from shorts_generator.utils import upload_to_s3
    from mail_sender import send_email
    from config import get_settings
    
    logger = logger.bind(name="ModalTask")
    settings = get_settings()
    
    transcriptions = []
    short_transcriptions = []
    shorts_v1_audio_path = []
    final_timestamps = []
    
    video_path = os.path.join(base_path, user_id, "video")
    audio_path = os.path.join(base_path, user_id, "audio")
    split_audio_path = os.path.join(base_path, user_id, "chunks")
    shorts_audio_path = os.path.join(base_path, user_id, "shorts_audio")
    shorts_v1 = os.path.join(base_path, user_id, "shorts_v1")
    shorts_v2 = os.path.join(base_path, user_id, "shorts_v2")

    os.makedirs(video_path, exist_ok=True)
    os.makedirs(audio_path, exist_ok=True)
    os.makedirs(split_audio_path, exist_ok=True)
    os.makedirs(shorts_audio_path, exist_ok=True)
    os.makedirs(shorts_v1, exist_ok=True)
    os.makedirs(shorts_v2, exist_ok=True)

    processor = VideoProcessor(
        video_url=video_url,
        video_path=video_path,
        audio_path=audio_path,
        split_audio_path=split_audio_path
    )

    output_video_path = processor.download_video()
    output_audio_path = processor.extarct_audio_from_video(output_video_path)
    audio_split_timestamps = processor.split_audio_in_chunks(output_audio_path)

    transcriber = AudioTranscriber()

    paths = [
        os.path.join(split_audio_path, f"split_audio{i + 1}.wav")
        for i in range(len(audio_split_timestamps))
    ]

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(transcriber.transcribe_file, path, i+1): path for i, path in enumerate(paths)}
        for future in as_completed(futures):
            try:
                transcriptions.append(future.result())
            except Exception as e:
                transcriptions.append({"error": str(e), "path": futures[future]})

    transcriptions.sort(key=lambda x: x["id"])

    agent = ShortsAgent(transcriptions, audio_split_timestamps)
    video_detailed_timestamps = agent.video_timestamps(shorts_time)

    shorts_path = processor.generate_shorts(video_detailed_timestamps, output_video_path, shorts_v1, shorts_v2)
    
    for id, path in enumerate(shorts_path):
        output_audio_path = processor.extarct_audio_from_video(
            path, shorts=True, id=id+1, output_shorts_path=shorts_audio_path
        )
        shorts_v1_audio_path.append(output_audio_path)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(transcriber.transcribe_short, path, i+1): path for i, path in enumerate(shorts_v1_audio_path)}
        for future in as_completed(futures):
            try:
                short_transcriptions.append(future.result())
            except Exception as e:
                short_transcriptions.append({"error": str(e), "path": futures[future]})

    short_transcriptions.sort(key=lambda x: x["id"])

    for short_transcription in short_transcriptions:
        timestamp = agent.enhance_video_timestamps(short_transcription)
        final_timestamps.append(timestamp)

    local_shorts_path = processor.generate_shorts(final_timestamps, shorts_path, shorts_v1, shorts_v2, final_shorts=True)

    s3_paths = upload_to_s3(local_shorts_path, user_id, task_id)

    # Send webhook notification with all data
    send_webhook_notification(
        user_id=user_id,
        task_id=task_id,
        shorts_data=s3_paths,
        user_email=user_email,
        video_url=video_url,
        shorts_time=shorts_time,
        transcriptions=transcriptions,
        short_transcriptions=short_transcriptions
    )

    logger.info("Removing User Saved local data of shorts generation")

    user_dir = f"{base_path}/{user_id}"
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)

    # Try to send email, but don't fail the task if it fails
    try:
        response = send_email(user_email, s3_paths)
        logger.info(f"Email sent successfully to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {e}")
        response = {"error": "Email sending failed", "details": str(e)}
         
    return response


@app.function(
    image=image,
    secrets=secrets,
)
@modal.asgi_app()
def fastapi_app():
    """
    FastAPI app running as a Modal web endpoint.
    """
    import sys
    sys.path.insert(0, "/root/src")
    
    from fastapi import FastAPI, Body, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi import UploadFile
    from pydantic import BaseModel
    from typing import List
    import uuid
    
    from model import QueryRequest
    from shorts_generator.utils import (
        upload_to_s3, 
        generate_presigned_post, 
        retrieve_from_s3, 
        delete_from_s3,
        initiate_multipart_upload,
        generate_presigned_url_for_part,
        complete_multipart_upload
    )
    from config import get_settings

    api = FastAPI()
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api.post("/uploadfile/")
    async def create_upload_file(user_id: str, file: UploadFile):
        uploaded_file_url = upload_to_s3(
            file_paths=file.file,
            user_id=user_id,
            filename=file.filename,
            file_upload=True
        )
        return uploaded_file_url

    @api.get("/get-upload-url/")
    async def get_upload_url(user_id: str, filename: str):
        """Generate a presigned POST URL for direct S3 upload (for files < 5GB)."""
        try:
            result = generate_presigned_post(user_id=user_id, filename=filename)
            return {
                "success": True,
                "url": result["url"],
                "fields": result["fields"],
                "final_url": result["final_url"],
                "s3_key": result["s3_key"],
                "sanitized_filename": result["sanitized_filename"],
                "content_type": result["content_type"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @api.post("/initiate-multipart-upload/")
    async def initiate_multipart(user_id: str, filename: str):
        """Initiate a multipart upload for large files."""
        try:
            result = initiate_multipart_upload(user_id=user_id, filename=filename)
            return {
                "success": True,
                "upload_id": result["upload_id"],
                "key": result["key"],
                "final_url": result["final_url"],
                "sanitized_filename": result["sanitized_filename"],
                "content_type": result["content_type"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @api.get("/get-multipart-upload-url/")
    async def get_multipart_upload_url(
        user_id: str, 
        upload_id: str, 
        part_number: int, 
        key: str
    ):
        """Generate a presigned URL for uploading a specific part of a multipart upload."""
        try:
            settings = get_settings()
            presigned_url = generate_presigned_url_for_part(
                bucket_name=settings.BUCKET_NAME,
                key=key,
                upload_id=upload_id,
                part_number=part_number
            )
            return {
                "success": True,
                "presigned_url": presigned_url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    class MultipartPart(BaseModel):
        part_number: int
        etag: str

    class CompleteMultipartRequest(BaseModel):
        upload_id: str
        key: str
        parts: List[MultipartPart]

    @api.post("/complete-multipart-upload/")
    async def complete_multipart(
        user_id: str = Query(..., description="User ID"),
        request: CompleteMultipartRequest = Body(...)  # JSON body
    ):
        """Complete a multipart upload after all parts have been uploaded."""
        try:
            from loguru import logger
            logger = logger.bind(name="CompleteMultipart")
            
            # Validate request
            if not request.parts or len(request.parts) == 0:
                return {
                    "success": False,
                    "error": "No parts provided for multipart upload completion"
                }
            
            settings = get_settings()
            
            # Validate and convert parts to format expected by boto3
            formatted_parts = []
            for part in request.parts:
                if not part.etag:
                    return {
                        "success": False,
                        "error": f"Missing ETag for part {part.part_number}"
                    }
                
                # Ensure ETag is properly formatted (S3 ETags are wrapped in quotes)
                etag = part.etag.strip()
                if not etag.startswith('"'):
                    etag = f'"{etag}"'
                
                formatted_parts.append({
                    "PartNumber": part.part_number,
                    "ETag": etag
                })
            
            # Sort parts by part number to ensure correct order
            formatted_parts.sort(key=lambda x: x["PartNumber"])
            
            logger.info(f"Completing multipart upload: user_id={user_id}, upload_id={request.upload_id}, key={request.key}, parts_count={len(formatted_parts)}")
            logger.debug(f"Parts: {formatted_parts[:3]}...")  # Log first 3 parts for debugging
            
            result = complete_multipart_upload(
                bucket_name=settings.BUCKET_NAME,
                key=request.key,
                upload_id=request.upload_id,
                parts=formatted_parts
            )
            return {
                "success": True,
                "final_url": result["final_url"],
                "etag": result["etag"]
            }
        except Exception as e:
            from loguru import logger
            logger = logger.bind(name="CompleteMultipart")
            logger.error(f"Error completing multipart upload: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    @api.post("/shorts")
    async def generate_shorts(request: QueryRequest):
        """Endpoint that triggers the background task in Modal."""
        import uuid
        
        user_id = request.user_id
        user_email = request.user_email
        video_url = str(request.video_url)
        shorts_time = request.shorts_time
        
        # Generate a task ID
        task_id = str(uuid.uuid4())
        
        # Call Modal function asynchronously
        generate_shorts_task.spawn(user_id, user_email, video_url, shorts_time, task_id)
        
        return {"message": f"Shorts generation has begun", "task_id": task_id}

    @api.post("/get-shorts/{user_id}/{task_id}")
    def get_shorts(user_id: str, task_id: str):
        """Endpoint to get shorts of a specific video"""
        shorts_links = retrieve_from_s3(user_id, task_id)
        return shorts_links

    @api.delete("/delete-media/{user_id}")
    def delete_media(user_id: str, file_key: str):
        """Delete a media file from S3 using the file key."""
        try:
            if not file_key.startswith(f"{user_id}/"):
                return {
                    "success": False,
                    "error": "File key must belong to the specified user"
                }
            
            success = delete_from_s3(user_id=user_id, file_key=file_key)
            
            if success:
                return {
                    "success": True,
                    "message": f"File {file_key} deleted successfully",
                    "deleted_file": file_key
                }
            else:
                return {
                    "success": False,
                    "error": "File not found or could not be deleted"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @api.delete("/delete-video/{user_id}")
    def delete_video(user_id: str, filename: str):
        """Delete a video file from S3 using just the filename."""
        try:
            file_key = f"{user_id}/video/{filename}"
            
            success = delete_from_s3(user_id=user_id, file_key=file_key)
            
            if success:
                return {
                    "success": True,
                    "message": f"Video {filename} deleted successfully",
                    "deleted_file": file_key
                }
            else:
                return {
                    "success": False,
                    "error": "Video not found or could not be deleted"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @api.post("/check-short-status/{task_id}")
    async def get_task_status(task_id: str):
        """Endpoint to check the status of the task."""
        # Note: Modal doesn't have a direct equivalent to Celery's AsyncResult
        # You might want to store task status in a database or use Modal's function status
        # For now, this is a placeholder
        return {
            "task_id": task_id,
            "status": "in progress",
            "note": "Use Modal dashboard to check task status"
        }

    return api

