from collections import Counter
from typing import List

from database import (
    cleanup_memory_store,
    get_recent_chat_history,
    get_unsummarized_chat_history,
    save_conversation_summary,
)


def _extract_topic_words(text: str) -> List[str]:
    stopwords = {
        "the", "and", "that", "with", "this", "have", "from", "what", "about", "your", "today",
        "just", "into", "want", "need", "would", "there", "them", "then", "when", "like", "feel",
        "because", "please", "could", "should", "been", "were", "they", "i", "you", "ava",
    }
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
    return [word for word in cleaned.split() if len(word) > 3 and word not in stopwords]


def maybe_refresh_conversation_summary() -> None:
    unsummarized = get_unsummarized_chat_history(batch_size=8)
    if len(unsummarized) < 6:
        return

    user_topics: Counter[str] = Counter()
    modes: Counter[str] = Counter()
    latest_user_message = ""

    for item in unsummarized:
        user_topics.update(_extract_topic_words(str(item.get("user_input", ""))))
        modes.update([str(item.get("mode", "casual"))])
        latest_user_message = str(item.get("user_input", "")) or latest_user_message

    top_topics = [topic for topic, _ in user_topics.most_common(4)]
    dominant_mode = modes.most_common(1)[0][0] if modes else "casual"
    summary_parts = []

    if top_topics:
        summary_parts.append("Recent recurring topics: " + ", ".join(top_topics) + ".")
    summary_parts.append(f"Recent conversation mode trend: {dominant_mode}.")
    if latest_user_message:
        summary_parts.append(f"Most recent user focus: {latest_user_message}")

    save_conversation_summary(
        " ".join(summary_parts),
        chat_ids=[int(item["id"]) for item in unsummarized],
        source="auto",
    )


def maintain_memory_system() -> None:
    maybe_refresh_conversation_summary()
    cleanup_memory_store()


def get_recent_chat_snapshot(limit: int = 3) -> List[str]:
    history = get_recent_chat_history(limit=limit)
    snapshots = []
    for item in history:
        snapshots.append(f"User said: {item.get('user_input', '')}")
    return snapshots
