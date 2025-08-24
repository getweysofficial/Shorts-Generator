from pydantic import BaseModel
from pydantic import EmailStr,HttpUrl


class QueryRequest(BaseModel):
    user_id: str
    user_email: EmailStr
    video_url:HttpUrl
    shorts_time:int
