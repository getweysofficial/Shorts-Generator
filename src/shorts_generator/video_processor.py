import urllib.request
import os
from moviepy import VideoFileClip


from loguru import logger
from scipy.io import wavfile


from config import get_settings



logger = logger.bind(name="VideoProcessor")
settings = get_settings()


class VideoProcessor:
    def __init__(self,video_url:str,video_path:str,audio_path:str,split_audio_path:str):
        self.video_url = video_url
        self.video_path = video_path
        self.audio_path = audio_path
        self.split_audio = split_audio_path 

        logger.info(f"VideoProcessor Initilized\n Audio Chunk: {settings.AUDIO_CHUNK_LENGTH} seconds\n Audio Overlap: {settings.AUDIO_OVERLAP_LENGTH} seconds")
        
    
    def download_video(self) -> str:
        """
        Download the video from the url
        """
        output_video_path = os.path.join(self.video_path,"video.mp4")

        urllib.request.urlretrieve(self.video_url,output_video_path)

        logger.info(f"\nVideo Saved to path: {output_video_path}")

        return output_video_path



    def extarct_audio_from_video(self,output_video_path:str) -> str:
        """
        Extract the audio in wav format from the video
        and delete the video after extraction.
        """

        clip = VideoFileClip(output_video_path)
        audio = clip.audio

        output_audio_path = os.path.join(self.audio_path,"audio.wav")

        audio.write_audiofile(output_audio_path)

        logger.info(f"\nAudio Saved to path: {output_audio_path}")

        # os.remove(output_video_path)

        # logger.info(f"\nRemoved the video file from path: {output_video_path}")

        return output_audio_path
    
    

    def split_audio_in_chunks(self,output_audio_path:str) -> list:
        """
        Splits the audio in to chunks and delete the audio after splitting
        """

        rate,data = wavfile.read(output_audio_path)

        split_at_timestamp = settings.AUDIO_CHUNK_LENGTH
        start = 0
        end = split_at_timestamp
        overlap = settings.AUDIO_OVERLAP_LENGTH
        count = 1
        split_at_frame_start = rate * start
        split_at_frame_end = rate * end
        audio_length = len(data)/rate

        audio_split_timestamps = []

        while True:

            audio_dict = {}

            split_audio = data[split_at_frame_start:split_at_frame_end]

            audio_dict["id"] = count
            audio_dict["start"] = start
            audio_dict["end"] = end
            audio_dict["overlap"] = 1

            audio_split_timestamps.append(audio_dict)

            wavfile.write(f'{self.split_audio}/split_audio{count}.wav', rate, split_audio)

            if end > audio_length:
                audio_split_timestamps[-1]["end"] = audio_length
                break

            start = end - overlap
            end = start + split_at_timestamp
            split_at_frame_start = rate * start
            split_at_frame_end = rate * end
            count +=1

        
        logger.info(f"\nAudio File is splitted into {len(audio_split_timestamps)} chunks")

        # os.remove(output_audio_path)

        # logger.info(f"\nRemoved the audio file from path: {output_audio_path}")

        print(audio_split_timestamps)

        return audio_split_timestamps








