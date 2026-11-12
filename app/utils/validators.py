import re
from typing import Optional


def validate_email_format(email: str) -> bool:
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    return len(username) >= 3 and bool(re.match(r'^[a-zA-Z0-9_-]+$', username))

