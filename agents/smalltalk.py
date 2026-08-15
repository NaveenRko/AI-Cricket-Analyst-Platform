import random
import re

GREETING_PATTERNS = [
    r"^\s*(hi+|hello+|hey+|yo|sup|hola)\s*[!.?]*\s*$",
    r"^\s*good\s*(morning|afternoon|evening|night)\s*[!.?]*\s*$",
    r"^\s*(hi|hello|hey)\s+(there|ipl analyst|analyst|bot)\s*[!.?]*\s*$",
    r"^\s*greetings\s*[!.?]*\s*$",
    r"^\s*what'?s\s*up\??\s*$",
    r"^\s*how\s*(are\s*you|r\s*u|is\s*it\s*going)\s*[!.?]*\s*$",
]

CLOSING_PATTERNS = [
    r"^\s*(bye+|goodbye|bye\s*bye|see\s*y(a|ou)|good\s*night)\s*[!.?]*\s*$",
    r"^\s*(thanks?|thank\s*you|thx|ty)\s*(so much|a lot)?\s*[!.?]*\s*$",
    r"^\s*(ok(ay)?\s*)?(bye|thanks|thank you)\s*[!.?]*\s*$",
    r"^\s*(that'?s\s*all|no more questions|i'?m done)\s*[!.?]*\s*$",
    r"^\s*talk\s*(later|soon)\s*[!.?]*\s*$",
]

GREETING_REPLIES = [
    "Hey! 👋 Ask me anything about IPL — batting, bowling, venues, matchups, records.",
    "Hi there! I'm your IPL analyst — what would you like to know?",
    "Hello! Ready when you are — ask me an IPL stat, player, or match question.",
    "Hey, good to see you. What IPL question can I dig into for you?",
]

CLOSING_REPLIES = [
    "Anytime! Come back whenever you've got another IPL question. 🏏",
    "You're welcome! Catch you next time.",
    "Glad to help — see you around!",
    "Sure thing. I'll be here whenever you want more IPL stats.",
]


def detect_smalltalk(question: str) -> dict | None:
    """
    Returns {"type": "greeting"|"closing", "answer": str} if the question is
    pure small talk, otherwise None (meaning: send it through the normal
    intent-classification pipeline).
    """
    q = question.strip().lower()
    q = re.sub(r"\s+", " ", q)

    for pattern in GREETING_PATTERNS:
        if re.match(pattern, q):
            return {"type": "greeting", "answer": random.choice(GREETING_REPLIES)}

    for pattern in CLOSING_PATTERNS:
        if re.match(pattern, q):
            return {"type": "closing", "answer": random.choice(CLOSING_REPLIES)}

    return None