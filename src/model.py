from pydantic import BaseModel


class QueryRequest(BaseModel):
    id:str
    video_url:str
    shorts_time:int


