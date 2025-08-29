from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore",env_file_encoding="utf-8")


    # -> Video Processing Configuration

    AUDIO_CHUNK_LENGTH: int = 120
    AUDIO_OVERLAP_LENGTH: int = 1

    # -> GEMINI Configuration

    GEMINI_API_KEY: str
    SHORTS_MODEL: str = "gemini-2.5-flash" 

    # -> GROQ CONFIGURATION

    GROQ_API_KEY: str
    AUDIO_TRANSCRIBE_MODEL: str = "whisper-large-v3-turbo"

    # AWS S3 BUCKET Configuration

    BUCKET_NAME: str
    AWS_REGION: str
    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str
    SUPABASE_ANON_KEY: str

    # Email Configuration
    SENDER_EMAIL_ADDRESS:str
    APP_PASSWORD:str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get the application settings.

    Returns:
        Settings: The application settings.
    """

    return Settings()

