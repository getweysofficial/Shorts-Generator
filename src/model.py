from pydantic import BaseModel


class QueryRequest(BaseModel):
    user_id: str
    user_email: str
    video_url:str
    shorts_time:int
