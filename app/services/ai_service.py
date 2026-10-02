from abc import ABC, abstractmethod
class AIService(ABC):
    @abstractmethod
    async def generate_response(self, message: str, conversation_history: list) -> str:
        raise NotImplementedError

