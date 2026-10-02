from pydantic import BaseModel
class Contact(BaseModel):
    id: int
    phone_number: str
    name: str | None = None
    email: str | None = None

