import os
import shutil
from celery import Celery
from concurrent.futures import ThreadPoolExecutor,as_completed

from loguru import logger

from shorts_generator.video_processor import VideoProcessor
from shorts_generator.audio_trancriber import AudioTranscriber
from shorts_generator.shorts_agent import ShortsAgent
from shorts_generator.utils import upload_to_s3

from mail_sender import send_email

logger = logger.bind("Celery Task")

celery = Celery(
     "worker",
     broker="redis://localhost:6379/0",
     backend="redis://localhost:6379/0"
)



base_path = "data"

@celery.task(bind=True)
def get_shorts_from_video(self,user_id,user_email,video_url,shorts_time):
    transcriptions = []
    short_transcriptions = []
    shorts_v1_audio_path = []
    final_timestamps = []
    task_id = self.request.id

    
    video_path = os.path.join(base_path,user_id,"video")
    audio_path = os.path.join(base_path,user_id,"audio")
    split_audio_path = os.path.join(base_path,user_id,"chunks")
    shorts_audio_path = os.path.join(base_path,user_id,"shorts_audio")
    shorts_v1 = os.path.join(base_path,user_id,"shorts_v1")
    shorts_v2 = os.path.join(base_path,user_id,"shorts_v2")

    os.makedirs(video_path, exist_ok=True)
    os.makedirs(audio_path, exist_ok=True)
    os.makedirs(split_audio_path, exist_ok=True)
    os.makedirs(shorts_audio_path,exist_ok=True)
    os.makedirs(shorts_v1,exist_ok=True)
    os.makedirs(shorts_v2,exist_ok=True)

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


    shorts_path = processor.generate_shorts(video_detailed_timestamps,output_video_path,shorts_v1,shorts_v2)
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

    local_shorts_path = processor.generate_shorts(final_timestamps,shorts_path,shorts_v1,shorts_v2,final_shorts=True)

    s3_paths = upload_to_s3(local_shorts_path,user_id,task_id)

    logger.info("Removing User Saved local data of shorts generation")

    user_dir = f"data/{user_id}"
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)

    response = send_email(user_email,s3_paths)
         
    return response