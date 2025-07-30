import json

from google import genai
from loguru import logger

from config import Settings
from shorts_generator.prompt import SHORTS_TOPIC_PROMPT


logger = logger.bind(name="TimeStampAgent")
settings = Settings()

class ShortsAgent:
    def __init__(self,transcriptions:list,timestamps:list):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.audio_transcriptions = transcriptions
        self.audio_split_timestamps = timestamps

        logger.info(f"ShortsAgent Agent Initilized\n TimeStamp Model: {settings.SHORTS_MODEL}")

    def video_timestamps(self):

        """
        Return the final json containing 
        detailed timestamps.

        """

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=SHORTS_TOPIC_PROMPT.format(self.audio_split_timestamps,self.audio_transcriptions),
        )

        lines = response.text.strip().splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

        print(response_text)

        logger.info("Succesfully generated timestamps")

        output = response_text

        processed_output = self.postprocess(output)

        return processed_output

        
    def postprocess(self,output):
        """
        Convert the string json into proper json
        """

        output = json.loads(output)

        logger.info("Succesfully Converted into json")


        return output
        





