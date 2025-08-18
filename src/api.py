
import click

from fastapi import FastAPI
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


@app.post("/shorts")
def generate_shorts(request:QueryRequest):
    """Endpoint that triggers the background task in Celery."""

    user_id = request.user_id
    user_email = request.user_email
    video_url = request.video_url
    shorts_time = request.shorts_time

    task = get_shorts_from_video.delay(user_id,user_email,video_url,shorts_time)

    return {"message": f"Shorts generation has begun", "task_id": task.id}


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