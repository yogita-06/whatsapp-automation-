import re
def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if not 7 <= len(digits) <= 15:
        raise ValueError("Invalid phone number")
    return f"+{digits}"

