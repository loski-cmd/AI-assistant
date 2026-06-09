from typing import Literal


ConversationMode = Literal["casual", "support", "market", "practical"]


def detect_conversation_mode(user_text: str) -> ConversationMode:
    lowered = user_text.lower().strip()

    support_markers = [
        "i feel",
        "i'm feeling",
        "i am feeling",
        "sad",
        "stressed",
        "anxious",
        "tired",
        "overwhelmed",
        "lonely",
        "upset",
        "not okay",
        "not ok",
        "depressed",
    ]
    market_markers = [
        "market",
        "forex",
        "crypto",
        "bitcoin",
        "btc",
        "gold",
        "usd",
        "trading",
        "bias",
        "sentiment",
        "war news",
        "geopolitical",
        "cot",
        "ict",
        "fed",
        "tariff",
    ]
    practical_markers = [
        "how do i",
        "how should i",
        "help me",
        "what should i do",
        "plan",
        "step by step",
        "organize",
        "fix",
        "build",
        "set up",
    ]

    if any(marker in lowered for marker in market_markers):
        return "market"

    if any(marker in lowered for marker in support_markers):
        return "support"

    if any(marker in lowered for marker in practical_markers):
        return "practical"

    return "casual"
