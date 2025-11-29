from typing import Optional

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    # conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    # conversation_id: str