from pydantic import BaseModel, Field

class IncomingMessage(BaseModel):
    message_id: str
    sender_phone: str
    message_type: str
    text: str = ""
    interactive_id: str | None = None
    timestamp: str | None = None

class OutgoingMessage(BaseModel):
    text: str
    state: str

class DemoMessageRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=25)
    message: str = Field(min_length=1, max_length=2000)

