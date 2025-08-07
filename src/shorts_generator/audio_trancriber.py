import os

from config import get_settings
from loguru import logger

from groq import Groq
from io import BytesIO


logger = logger.bind(name="AudioTranscriber")
settings = get_settings()

class AudioTranscriber:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)


        logger.info(f"AudioTranscriber Initilized\n Audio Transcriber Model: {settings.AUDIO_TRANSCRIBE_MODEL}")


        
    def transcribe_file(self,audio_path,id):
        """
        Transcribe the audio chunks and removed the transcribe audio chunk
        """


        with open(audio_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model=settings.AUDIO_TRANSCRIBE_MODEL,
            response_format="verbose_json"
            )

            single_transcript = {}

            single_transcript["id"] = id
            single_transcript["text"] = transcription.text
            single_transcript["text_with_timestamps"] = [ 
            {
                "id": item["id"],
                "start": item["start"],
                "end": item["end"],
                "text": item["text"]
            } 
        
            for item in transcription.segments]


            logger.info(f"\nAudio {id} trasncribed successfully")

            # os.remove(audio_path)

            # logger.info(f"\nAudio {id} removed from path: {audio_path}")

        return single_transcript
    
    def transcribe_short(self,audio_path,id):
        """
        Transcribe the short audio chunks 
        """
        print("audio_path: ",audio_path)
        with open(audio_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model=settings.AUDIO_TRANSCRIBE_MODEL,
            response_format="verbose_json",
            timestamp_granularities=["word"]
            )

            single_transcript = {}

            single_transcript["id"] = id
            single_transcript["text"] = transcription.text
            single_transcript["word_with_timestamps"] = [ 
            {
                "start": item["start"],
                "end": item["end"],
                "word": item["word"]
            } 
        
            for item in transcription.words]


            logger.info(f"\nAudio {id} trasncribed successfully")

            # os.remove(audio_path)

            # logger.info(f"\nAudio {id} removed from path: {audio_path}")

        return single_transcript