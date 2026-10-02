from enum import StrEnum
from pydantic import BaseModel

class ConversationState(StrEnum):
    NEW = "NEW"
    MAIN_MENU = "MAIN_MENU"
    WAITING_FOR_NAME = "WAITING_FOR_NAME"
    WAITING_FOR_TREATMENT = "WAITING_FOR_TREATMENT"
    WAITING_FOR_DATE = "WAITING_FOR_DATE"
    WAITING_FOR_TIME = "WAITING_FOR_TIME"
    REVIEW_APPOINTMENT = "REVIEW_APPOINTMENT"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    COMPLETED = "COMPLETED"

class Conversation(BaseModel):
    id: int
    contact_id: int
    current_state: ConversationState
    automation_enabled: bool = True
    draft: dict = {}

