import os
import click

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from concurrent.futures import ThreadPoolExecutor,as_completed

from shorts_generator.video_processor import VideoProcessor
from shorts_generator.audio_trancriber import AudioTranscriber
from shorts_generator.shorts_agent import ShortsAgent

from model import QueryRequest



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_path = "data"

@app.post("/shorts")
async def get_shorts_from_video(request:QueryRequest):
    transcriptions = []
    short_transcriptions = []
    shorts_v1_audio_path = []
    final_timestamps = []

    video_url = request.video_url
    shorts_time = request.shorts_time
    video_path = os.path.join(base_path,"video")
    audio_path = os.path.join(base_path,"audio")
    split_audio_path = os.path.join(base_path,"chunks")
    shorts_audio_path = os.path.join(base_path,"shorts_audio")

    os.makedirs(video_path, exist_ok=True)
    os.makedirs(audio_path, exist_ok=True)
    os.makedirs(split_audio_path, exist_ok=True)
    os.makedirs(shorts_audio_path,exist_ok=True)

    processor = VideoProcessor(video_url=video_url,video_path=video_path,audio_path=audio_path,split_audio_path=split_audio_path)

    output_video_path = processor.download_video()
    output_audio_path = processor.extarct_audio_from_video(output_video_path)
    audio_split_timestamps = processor.split_audio_in_chunks(output_audio_path)

    transcriber = AudioTranscriber()

    paths = [
        os.path.join(split_audio_path, f"split_audio{i + 1}.wav")
        for i in range(len(audio_split_timestamps))
    ]

    with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(transcriber.transcribe_file, path,i+1): path for i,path in enumerate(paths)}
            for future in as_completed(futures):
                try:
                    transcriptions.append(future.result())
                except Exception as e:
                    transcriptions.append({"error": str(e), "path": futures[future]})


    transcriptions.sort(key=lambda x: x["id"])

    agent = ShortsAgent(transcriptions,audio_split_timestamps)

    video_detailed_timestamps = agent.video_timestamps(shorts_time)


    shorts_path = processor.generate_shorts(video_detailed_timestamps,output_video_path)
    for id,path in enumerate(shorts_path):
        output_audio_path = processor.extarct_audio_from_video(path,shorts=True,id=id+1,output_shorts_path=shorts_audio_path)
        shorts_v1_audio_path.append(output_audio_path)

    

    with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(transcriber.transcribe_short, path,i+1): path for i,path in enumerate(shorts_v1_audio_path)}
            for future in as_completed(futures):
                try:
                    short_transcriptions.append(future.result())
                except Exception as e:
                    short_transcriptions.append({"error": str(e), "path": futures[future]})

    short_transcriptions.sort(key=lambda x:x["id"])

    for short_transcription in short_transcriptions:
         timestamp = agent.enhance_video_timestamps(short_transcription)
         final_timestamps.append(timestamp)

    final_shorts_path = processor.generate_shorts(final_timestamps,shorts_path,final_shorts=True)
         
    return final_shorts_path



@click.command()
@click.option("--port",default=8080,help="FastAPI server port")
@click.option("--host",default="0.0.0.0",help="FastAPI server host")

def run_api(port,host):
    import uvicorn

    uvicorn.run("api:app",host=host,port=port,loop="asyncio")

if __name__ == "__main__":
    run_api()