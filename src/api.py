
import click

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from celery.result import AsyncResult


from task import get_shorts_from_video

from model import QueryRequest



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/uploadfile/")
async def create_upload_file(user_id: str, file: UploadFile):
    from shorts_generator.utils import upload_to_s3

    uploaded_file_url = upload_to_s3(file_paths=file.file,user_id=user_id,filename=file.filename,file_upload=True)

    return uploaded_file_url

@app.post("/get-upload-url/")
async def get_upload_url(user_id: str, filename: str):
    """Generate a presigned URL for direct S3 upload."""
    from shorts_generator.utils import generate_presigned_upload_url
    
    try:
        result = generate_presigned_upload_url(user_id=user_id, filename=filename)
        return {
            "success": True,
            "presigned_url": result["presigned_url"],
            "final_url": result["final_url"],
            "s3_key": result["s3_key"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/shorts")
def generate_shorts(request:QueryRequest):
    """Endpoint that triggers the background task in Celery."""

    user_id = request.user_id
    user_email = request.user_email
    video_url = request.video_url
    shorts_time = request.shorts_time

    task = get_shorts_from_video.delay(user_id,user_email,video_url,shorts_time)

    return {"message": f"Shorts generation has begun", "task_id": task.id}


@app.post("/get-shorts/{user_id}/{task_id}")
def get_shorts(user_id: str,task_id: str):
    "Endpoint to get shorts of a specific video"

    from shorts_generator.utils import retrieve_from_s3
    
    shorts_links = retrieve_from_s3(user_id,task_id)

    return shorts_links
    


@app.post("/check-short-status/{task_id}")
def get_task_status(task_id: str):
    """Endpoint to check the status of the task."""
    task_result = AsyncResult(task_id) 
    if task_result.ready():  
        return {"task_id": task_id, "status": "completed", "result": task_result.result}
    elif task_result.failed(): 
        return {"task_id": task_id, "status": "failed"}
    else: 
        return {"task_id": task_id, "status": "in progress"}


@click.command()
@click.option("--port",default=8080,help="FastAPI server port")
@click.option("--host",default="0.0.0.0",help="FastAPI server host")

def run_api(port,host):
    import uvicorn

    uvicorn.run("api:app",host=host,port=port,loop="asyncio")

if __name__ == "__main__":
    run_api()