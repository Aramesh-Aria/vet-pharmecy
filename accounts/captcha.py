"""A lightweight, self-hosted math captcha.

Google reCAPTCHA / hCaptcha are unreliable in Iran, so we use a simple
server-side arithmetic challenge kept in the session. ``new_question`` stores the
answer and returns the (Persian-digit) question; ``check`` validates the user's
answer, accepting Persian or ASCII digits.
"""
import secrets

ANSWER_SESSION_KEY = "captcha_answer"

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_TO_ASCII = {ord(p): str(i) for i, p in enumerate("۰۱۲۳۴۵۶۷۸۹")}
_TO_ASCII.update({ord(a): str(i) for i, a in enumerate("٠١٢٣٤٥٦٧٨٩")})


def new_question(session) -> str:
    """Generate a fresh challenge, store its answer in *session*, and return the
    question to display (with Persian digits)."""
    a = secrets.randbelow(9) + 1
    b = secrets.randbelow(9) + 1
    session[ANSWER_SESSION_KEY] = a + b
    return f"{a} + {b}".translate(_FA)


def check(session, value) -> bool:
    answer = session.get(ANSWER_SESSION_KEY)
    if answer is None:
        return False
    try:
        given = int(str(value).strip().translate(_TO_ASCII))
    except (TypeError, ValueError):
        return False
    return given == answer
