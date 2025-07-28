import click

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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
async def get_shorts_from_video(request:QueryRequest):
    video_url = request.video_url
    return video_url





@click.command()
@click.option("--port",default=8080,help="FastAPI server port")
@click.option("--host",default="0.0.0.0",help="FastAPI server host")

def run_api(port,host):
    import uvicorn

    uvicorn.run("api:app",host=host,port=port,loop="asyncio")

if __name__ == "__main__":
    run_api()