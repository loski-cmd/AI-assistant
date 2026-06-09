import re
from typing import List

from database import (
    get_user_preference,
    save_long_term_memory,
    save_user_preference,
)


def extract_and_store_memories(user_text: str) -> List[str]:
    text = user_text.strip()
    lowered = text.lower()
    saved_items: List[str] = []

    preferred_name_match = re.search(r"\b(?:my name is|i am|i'm)\s+([A-Z][a-z]+)\b", text)
    if preferred_name_match and len(preferred_name_match.group(1)) > 1:
        save_long_term_memory(
            "identity",
            f"User may prefer to be called {preferred_name_match.group(1)}.",
            importance=4,
            source="auto",
            tags=["name", "identity"],
        )
        saved_items.append("memory:name")

    tone_match = re.search(r"\bi (?:prefer|like) (?:a |an )?(calm|gentle|direct|warm|brief|short) tone\b", lowered)
    if tone_match:
        tone = tone_match.group(1)
        if get_user_preference("tone") != tone:
            save_user_preference("tone", tone, source="auto")
            saved_items.append(f"preference:tone={tone}")

    if "call me " in lowered:
        name = text[lowered.index("call me ") + len("call me "):].strip(" .,!?\n")
        if name:
            save_long_term_memory(
                "identity",
                f"User prefers to be called {name}.",
                importance=5,
                source="auto",
                tags=["name", "identity"],
            )
            saved_items.append("memory:preferred_name")

    for phrase, key in [
        ("i like short replies", "reply_length"),
        ("keep it short", "reply_length"),
        ("be direct", "style"),
        ("be brief", "reply_length"),
    ]:
        if phrase in lowered:
            value = "short" if "short" in phrase or "brief" in phrase else "direct"
            save_user_preference(key, value, source="auto")
            saved_items.append(f"preference:{key}")

    routine_match = re.search(r"\bi usually ([^.?!]+)", lowered)
    if routine_match:
        save_long_term_memory(
            "routine",
            f"User routine note: {routine_match.group(1).strip()}",
            importance=3,
            source="auto",
            tags=["routine"],
        )
        saved_items.append("memory:routine")

    goal_match = re.search(r"\bmy goal is to ([^.?!]+)", lowered)
    if goal_match:
        save_long_term_memory(
            "goals",
            f"User goal: {goal_match.group(1).strip()}",
            importance=4,
            source="auto",
            tags=["goal"],
        )
        saved_items.append("memory:goal")

    likes_match = re.search(r"\bi like ([^.?!]+)", lowered)
    if likes_match and "tone" not in lowered:
        save_long_term_memory(
            "preferences",
            f"User likes {likes_match.group(1).strip()}",
            importance=3,
            source="auto",
            tags=["likes"],
        )
        saved_items.append("memory:likes")

    if any(phrase in lowered for phrase in ["i trade", "i'm trading", "i am trading", "my trading style"]):
        save_long_term_memory(
            "trading",
            f"User said: {text}",
            importance=4,
            source="auto",
            tags=["trading"],
        )
        saved_items.append("memory:trading")

    if any(asset in lowered for asset in ["gold", "btc", "bitcoin", "usd", "forex", "crypto"]):
        current_assets = get_user_preference("assets") or ""
        current_lower = current_assets.lower()
        asset_map = {
            "gold": "gold",
            "btc": "btc",
            "bitcoin": "bitcoin",
            "usd": "usd",
            "forex": "forex",
            "crypto": "crypto",
        }
        discovered_assets = [
            normalized
            for keyword, normalized in asset_map.items()
            if keyword in lowered and normalized not in current_lower
        ]
        if discovered_assets:
            combined = [item.strip() for item in current_assets.split(",") if item.strip()]
            combined.extend(discovered_assets)
            deduped: List[str] = []
            for item in combined:
                if item.lower() not in [entry.lower() for entry in deduped]:
                    deduped.append(item)
            save_user_preference("assets", ", ".join(deduped), source="auto")
            saved_items.append("preference:assets")

    if any(phrase in lowered for phrase in ["war news", "geopolitical", "political events", "market sentiment"]):
        save_long_term_memory(
            "trading",
            "User is highly interested in geopolitical and political events that affect market sentiment.",
            importance=5,
            source="auto",
            tags=["macro", "geopolitical", "market"],
        )
        saved_items.append("memory:macro_focus")

    return saved_items
