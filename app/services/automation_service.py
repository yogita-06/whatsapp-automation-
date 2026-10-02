import re
import uuid
from app.core.clinic_config import CLINIC_NAME, CLINIC_HOURS, TREATMENTS, TREATMENT_OVERVIEW, TIME_SLOTS
from app.models.conversation import ConversationState as State
from app.repositories.store import Store

MENU = f"Welcome to {CLINIC_NAME} 👋\n\nHow can we help you today?\n\n1. Book Appointment\n2. View Treatments\n3. Clinic Hours\n4. Talk to Staff"
TREATMENT_PROMPT = "Which treatment are you interested in?\n\n" + "\n".join(f"{k}. {v}" for k,v in TREATMENTS.items())
TIME_PROMPT = "What time would you prefer?\n\n" + "\n".join(f"{k}. {v}" for k,v in TIME_SLOTS.items())

class AutomationService:
    def __init__(self, store: Store): self.store = store
    async def process(self, phone: str, message: str, message_id: str | None = None, message_type: str = "text") -> tuple[str | None, State, bool]:
        contact, conv = await self.store.get_or_create_session(phone)
        if message_id and await self.store.message_exists(message_id): return None, State(conv["current_state"]), True
        await self.store.add_message(contact["id"], message_id, "incoming", message_type, message)
        state, draft = State(conv["current_state"]), conv["draft"]
        command = message.strip().upper()
        if command in {"MENU", "START"}:
            state, draft, reply, enabled = State.MAIN_MENU, {}, MENU, True
        elif command in {"RESET", "CANCEL"}:
            state, draft, reply, enabled = State.MAIN_MENU, {}, "Your current request has been cleared.\n\n" + MENU, True
        elif not conv["automation_enabled"]:
            return None, State.WAITING_FOR_HUMAN, False
        elif message_type not in {"text", "interactive"}:
            reply, enabled = "Thanks for sending that. This demo currently supports text-based conversations. Please type your request or send MENU.", True
        elif self._severe(message):
            reply, enabled = "This may need urgent attention. Please contact a dental professional or local emergency service promptly. Would you like to request an appointment or talk to staff?\n\n1. Request Appointment\n2. Talk to Staff", True
        elif self._pain(message):
            reply, enabled = "I'm sorry you're experiencing that. Dental pain can have different causes and should be assessed by a dental professional.\n\nWould you like to request an appointment or speak with the clinic?\n\n1. Request Appointment\n2. Talk to Staff", True
        elif state in {State.NEW, State.COMPLETED}:
            state, draft, reply, enabled = State.MAIN_MENU, {}, MENU, True
        elif state == State.MAIN_MENU:
            selection = self._menu_choice(message)
            if selection == "book": state, draft, reply, enabled = State.WAITING_FOR_NAME, {}, "Sure. May I know your name?", True
            elif selection == "treatments": reply, enabled = "Our demo clinic offers:\n\n" + "\n".join(f"• {x}" for x in TREATMENT_OVERVIEW) + "\n\nType MENU anytime to return to the main menu.", True
            elif selection == "hours": reply, enabled = "Clinic hours:\n\n" + "\n".join(f"{d}: {h}" for d,h in CLINIC_HOURS.items()) + "\n\nType MENU anytime to return to the main menu.", True
            elif selection == "human": state, reply, enabled = State.WAITING_FOR_HUMAN, "Of course. I've marked this conversation for human assistance. A team member can continue from here.", False
            else: reply, enabled = "Please choose 1, 2, 3, or 4.\n\n" + MENU, True
        elif state == State.WAITING_FOR_NAME:
            name = message.strip()
            if not 2 <= len(name) <= 80 or not re.fullmatch(r"[\w .'-]+", name, re.UNICODE): reply, enabled = "Please enter a valid name (2–80 characters).", True
            else:
                draft["name"] = name; await self.store.update_name(contact["id"], name)
                state, reply, enabled = State.WAITING_FOR_TREATMENT, f"Thanks {name}. {TREATMENT_PROMPT}", True
        elif state == State.WAITING_FOR_TREATMENT:
            treatment = self._option(message, TREATMENTS)
            if not treatment: reply, enabled = "Please choose a treatment by number or name.\n\n" + TREATMENT_PROMPT, True
            else: draft["treatment"] = treatment; state, reply, enabled = State.WAITING_FOR_DATE, "What is your preferred appointment date?\n\nFor example: Tomorrow, Monday, 25 September, or 2026-09-30.", True
        elif state == State.WAITING_FOR_DATE:
            date = message.strip()
            if not 2 <= len(date) <= 80: reply, enabled = "Please enter a preferred date.", True
            else: draft["date"] = date; state, reply, enabled = State.WAITING_FOR_TIME, TIME_PROMPT, True
        elif state == State.WAITING_FOR_TIME:
            time = self._option(message, TIME_SLOTS)
            if not time: reply, enabled = "Please choose a time by number or enter one of the listed times.\n\n" + TIME_PROMPT, True
            else:
                draft["time"] = time; draft["request_key"] = draft.get("request_key", uuid.uuid4().hex)
                state, reply, enabled = State.REVIEW_APPOINTMENT, self._review(draft), True
        else:
            choice = message.strip().lower()
            if choice in {"1", "confirm", "confirm request"}:
                await self.store.create_appointment(contact, draft, draft["request_key"])
                state, enabled = State.COMPLETED, True
                reply = f"Thanks {draft['name']}.\n\nYour appointment request has been received.\n\nRequested:\n{draft['treatment']}\n{draft['date']}\n{draft['time']}\n\nThe clinic team will confirm the final appointment separately."
            elif choice in {"2", "start again"}: state, draft, reply, enabled = State.WAITING_FOR_NAME, {}, "Sure. May I know your name?", True
            elif choice in {"3", "talk to staff"}: state, reply, enabled = State.WAITING_FOR_HUMAN, "Of course. I've marked this conversation for human assistance. A team member can continue from here.", False
            else: reply, enabled = "Please choose 1 to confirm, 2 to start again, or 3 to talk to staff.\n\n" + self._review(draft), True
        await self.store.update_conversation(contact["id"], state, draft, enabled)
        await self.store.add_message(contact["id"], None, "outgoing", "text", reply)
        return reply, state, False
    @staticmethod
    def _option(value: str, options: dict[str,str]) -> str | None:
        clean = value.strip().casefold()
        if clean in options: return options[clean]
        return next((v for v in options.values() if v.casefold() == clean), None)
    @staticmethod
    def _menu_choice(value: str) -> str | None:
        clean = value.strip().casefold()
        choices = {"1":"book","book appointment":"book","request appointment":"book","2":"treatments","view treatments":"treatments","3":"hours","clinic hours":"hours","4":"human","talk to staff":"human"}
        return choices.get(clean)
    @staticmethod
    def _review(d: dict) -> str:
        return f"Please review your appointment request:\n\nName: {d['name']}\nTreatment: {d['treatment']}\nPreferred Date: {d['date']}\nPreferred Time: {d['time']}\n\n1. Confirm Request\n2. Start Again\n3. Talk to Staff"
    @staticmethod
    def _pain(value: str) -> bool: return any(x in value.casefold() for x in ("tooth pain", "tooth hurts", "tooth is hurting", "dental pain"))
    @staticmethod
    def _severe(value: str) -> bool: return any(x in value.casefold() for x in ("severe", "unbearable", "heavy bleeding", "can't breathe", "cannot breathe", "swelling face"))

