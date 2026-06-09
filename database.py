import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from config import MEMORY_STORE_PATH


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_store() -> Dict[str, object]:
    return {
        "store_version": 2,
        "next_chat_id": 1,
        "next_memory_id": 1,
        "next_summary_id": 1,
        "chat_memory": [],
        "user_profile": None,
        "long_term_memory": [],
        "user_preferences": {},
        "conversation_summaries": [],
    }


def _read_store() -> Dict[str, object]:
    if not MEMORY_STORE_PATH.exists():
        return _default_store()

    with open(MEMORY_STORE_PATH, "r", encoding="utf-8-sig") as file:
        return json.load(file)


def _write_store(store: Dict[str, object]) -> None:
    with open(MEMORY_STORE_PATH, "w", encoding="utf-8") as file:
        json.dump(store, file, indent=2)


def _normalize_preferences(raw_preferences: object) -> Dict[str, Dict[str, str]]:
    normalized: Dict[str, Dict[str, str]] = {}
    now = _now_iso()

    if isinstance(raw_preferences, dict):
        for key, value in raw_preferences.items():
            if isinstance(value, dict):
                normalized[key] = {
                    "value": str(value.get("value", "")),
                    "source": str(value.get("source", "manual")),
                    "updated_at": str(value.get("updated_at", now)),
                }
            else:
                normalized[key] = {
                    "value": str(value),
                    "source": "legacy",
                    "updated_at": now,
                }

    return normalized


def init_database() -> None:
    store = _default_store()
    existing = _read_store()
    store.update(existing)

    now = _now_iso()

    normalized_chats: List[Dict[str, object]] = []
    next_chat_id = 1
    for item in store.get("chat_memory", []):
        if not isinstance(item, dict):
            continue
        chat_id = int(item.get("id", next_chat_id))
        next_chat_id = max(next_chat_id, chat_id + 1)
        normalized_chats.append(
            {
                "id": chat_id,
                "user_input": str(item.get("user_input", "")),
                "ai_response": str(item.get("ai_response", "")),
                "mode": str(item.get("mode", "casual")),
                "created_at": str(item.get("created_at", now)),
            }
        )

    normalized_memories: List[Dict[str, object]] = []
    next_memory_id = 1
    for item in store.get("long_term_memory", []):
        if not isinstance(item, dict):
            continue
        memory_id = int(item.get("id", next_memory_id))
        next_memory_id = max(next_memory_id, memory_id + 1)
        normalized_memories.append(
            {
                "id": memory_id,
                "category": str(item.get("category", "general")),
                "content": str(item.get("content", "")),
                "importance": int(item.get("importance", 3)),
                "source": str(item.get("source", "manual")),
                "created_at": str(item.get("created_at", now)),
                "updated_at": str(item.get("updated_at", item.get("created_at", now))),
                "last_used_at": item.get("last_used_at"),
                "tags": list(item.get("tags", [])),
                "archived": bool(item.get("archived", False)),
            }
        )

    normalized_summaries: List[Dict[str, object]] = []
    next_summary_id = 1
    for item in store.get("conversation_summaries", []):
        if not isinstance(item, dict):
            continue
        summary_id = int(item.get("id", next_summary_id))
        next_summary_id = max(next_summary_id, summary_id + 1)
        normalized_summaries.append(
            {
                "id": summary_id,
                "summary": str(item.get("summary", "")),
                "source": str(item.get("source", "auto")),
                "created_at": str(item.get("created_at", now)),
                "chat_ids": list(item.get("chat_ids", [])),
            }
        )

    store["chat_memory"] = normalized_chats
    store["long_term_memory"] = normalized_memories
    store["user_preferences"] = _normalize_preferences(store.get("user_preferences", {}))
    store["conversation_summaries"] = normalized_summaries
    store["next_chat_id"] = max(int(store.get("next_chat_id", 1)), next_chat_id)
    store["next_memory_id"] = max(int(store.get("next_memory_id", 1)), next_memory_id)
    store["next_summary_id"] = max(int(store.get("next_summary_id", 1)), next_summary_id)
    store["store_version"] = 2
    _write_store(store)


def _extract_keywords(text: str) -> Set[str]:
    stopwords = {
        "the", "and", "that", "with", "this", "have", "from", "what", "about", "your", "today",
        "just", "into", "want", "need", "would", "there", "them", "then", "when", "like", "feel",
        "because", "market", "assistant", "please", "could", "should", "been", "were", "they",
    }
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
    return {word for word in cleaned.split() if len(word) > 2 and word not in stopwords}


def save_chat_memory(user_input: str, ai_response: str, mode: str = "casual") -> Dict[str, object]:
    store = _read_store()
    chat_entry = {
        "id": int(store.get("next_chat_id", 1)),
        "user_input": user_input,
        "ai_response": ai_response,
        "mode": mode,
        "created_at": _now_iso(),
    }
    store["next_chat_id"] = chat_entry["id"] + 1
    store.setdefault("chat_memory", []).append(chat_entry)
    _write_store(store)
    return chat_entry


def get_recent_chat_history(limit: int = 5) -> List[Dict[str, object]]:
    store = _read_store()
    history = store.get("chat_memory", [])
    return history[-limit:]


def save_user_profile(name: str, mood: str, trading_goal: str) -> None:
    store = _read_store()
    store["user_profile"] = {
        "name": name,
        "mood": mood,
        "trading_goal": trading_goal,
        "updated_at": _now_iso(),
    }
    _write_store(store)


def load_user_profile() -> Optional[Dict[str, str]]:
    store = _read_store()
    return store.get("user_profile")


def save_long_term_memory(
    category: str,
    content: str,
    importance: int = 3,
    source: str = "manual",
    tags: Optional[List[str]] = None,
) -> Dict[str, object]:
    bounded_importance = max(1, min(5, importance))
    normalized_content = content.strip().lower()
    store = _read_store()
    memories = store.setdefault("long_term_memory", [])
    now = _now_iso()

    for memory in memories:
        if memory.get("archived"):
            continue
        same_category = memory.get("category", "").strip().lower() == category.strip().lower()
        same_content = memory.get("content", "").strip().lower() == normalized_content
        if same_category and same_content:
            memory["importance"] = max(int(memory.get("importance", 3)), bounded_importance)
            memory["source"] = source
            memory["updated_at"] = now
            memory["tags"] = sorted(set(memory.get("tags", [])) | set(tags or []))
            _write_store(store)
            return memory

    memory_entry = {
        "id": int(store.get("next_memory_id", 1)),
        "category": category,
        "content": content,
        "importance": bounded_importance,
        "source": source,
        "created_at": now,
        "updated_at": now,
        "last_used_at": None,
        "tags": sorted(set(tags or [])),
        "archived": False,
    }
    store["next_memory_id"] = memory_entry["id"] + 1
    memories.append(memory_entry)
    _write_store(store)
    return memory_entry


def update_long_term_memory(
    memory_id: int,
    *,
    category: Optional[str] = None,
    content: Optional[str] = None,
    importance: Optional[int] = None,
    tags: Optional[List[str]] = None,
    archived: Optional[bool] = None,
) -> bool:
    store = _read_store()
    for memory in store.get("long_term_memory", []):
        if int(memory.get("id", -1)) != memory_id:
            continue
        if category is not None:
            memory["category"] = category
        if content is not None:
            memory["content"] = content
        if importance is not None:
            memory["importance"] = max(1, min(5, importance))
        if tags is not None:
            memory["tags"] = sorted(set(tags))
        if archived is not None:
            memory["archived"] = archived
        memory["updated_at"] = _now_iso()
        _write_store(store)
        return True
    return False


def delete_long_term_memory(memory_id: int) -> bool:
    store = _read_store()
    memories = store.get("long_term_memory", [])
    filtered = [item for item in memories if int(item.get("id", -1)) != memory_id]
    if len(filtered) == len(memories):
        return False
    store["long_term_memory"] = filtered
    _write_store(store)
    return True


def get_long_term_memories(limit: Optional[int] = 5, include_archived: bool = False) -> List[Dict[str, object]]:
    store = _read_store()
    memories = [
        item
        for item in store.get("long_term_memory", [])
        if include_archived or not item.get("archived", False)
    ]
    sorted_memories = sorted(
        memories,
        key=lambda item: (
            int(item.get("importance", 3)),
            item.get("last_used_at") or "",
            item.get("updated_at") or "",
        ),
        reverse=True,
    )
    if limit is None:
        return sorted_memories
    return sorted_memories[:limit]


def get_relevant_long_term_memories(user_text: str, limit: int = 5) -> List[Dict[str, object]]:
    keywords = _extract_keywords(user_text)
    memories = get_long_term_memories(limit=None)
    scored: List[Dict[str, object]] = []
    for memory in memories:
        haystack = f"{memory.get('category', '')} {memory.get('content', '')} {' '.join(memory.get('tags', []))}"
        memory_keywords = _extract_keywords(haystack)
        overlap = len(keywords & memory_keywords)
        score = overlap * 4 + int(memory.get("importance", 3))
        if overlap > 0 or int(memory.get("importance", 3)) >= 4:
            memory_copy = dict(memory)
            memory_copy["_score"] = score
            scored.append(memory_copy)

    relevant = sorted(scored, key=lambda item: (item["_score"], item.get("updated_at", "")), reverse=True)[:limit]
    if relevant:
        mark_memories_used([int(item["id"]) for item in relevant])
    return [{key: value for key, value in item.items() if key != "_score"} for item in relevant]


def mark_memories_used(memory_ids: List[int]) -> None:
    store = _read_store()
    now = _now_iso()
    target_ids = set(memory_ids)
    changed = False
    for memory in store.get("long_term_memory", []):
        if int(memory.get("id", -1)) in target_ids:
            memory["last_used_at"] = now
            changed = True
    if changed:
        _write_store(store)


def save_user_preference(preference_key: str, preference_value: str, source: str = "manual") -> None:
    store = _read_store()
    preferences = store.setdefault("user_preferences", {})
    preferences[preference_key] = {
        "value": preference_value,
        "source": source,
        "updated_at": _now_iso(),
    }
    _write_store(store)


def delete_user_preference(preference_key: str) -> bool:
    store = _read_store()
    preferences = store.get("user_preferences", {})
    if preference_key not in preferences:
        return False
    del preferences[preference_key]
    _write_store(store)
    return True


def get_user_preference(preference_key: str) -> Optional[str]:
    store = _read_store()
    preferences = store.get("user_preferences", {})
    item = preferences.get(preference_key)
    if isinstance(item, dict):
        return item.get("value")
    if item is None:
        return None
    return str(item)


def get_user_preferences(limit: int = 5) -> List[Dict[str, str]]:
    store = _read_store()
    preferences = store.get("user_preferences", {})
    items = [
        {
            "key": key,
            "value": value.get("value", ""),
            "source": value.get("source", "manual"),
            "updated_at": value.get("updated_at", ""),
        }
        for key, value in preferences.items()
    ]
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return items[:limit]


def save_conversation_summary(summary: str, chat_ids: List[int], source: str = "auto") -> Dict[str, object]:
    store = _read_store()
    normalized_chat_ids = sorted(set(chat_ids))
    for existing in store.get("conversation_summaries", []):
        if sorted(existing.get("chat_ids", [])) == normalized_chat_ids:
            existing["summary"] = summary
            existing["source"] = source
            existing["created_at"] = _now_iso()
            _write_store(store)
            return existing

    summary_entry = {
        "id": int(store.get("next_summary_id", 1)),
        "summary": summary,
        "source": source,
        "created_at": _now_iso(),
        "chat_ids": normalized_chat_ids,
    }
    store["next_summary_id"] = summary_entry["id"] + 1
    store.setdefault("conversation_summaries", []).append(summary_entry)
    _write_store(store)
    return summary_entry


def get_conversation_summaries(limit: int = 5) -> List[Dict[str, object]]:
    store = _read_store()
    summaries = store.get("conversation_summaries", [])
    return sorted(summaries, key=lambda item: item.get("created_at", ""), reverse=True)[:limit]


def get_relevant_conversation_summaries(user_text: str, limit: int = 2) -> List[Dict[str, object]]:
    keywords = _extract_keywords(user_text)
    summaries = get_conversation_summaries(limit=20)
    scored: List[Dict[str, object]] = []
    for summary in summaries:
        overlap = len(keywords & _extract_keywords(summary.get("summary", "")))
        score = overlap * 3 + len(summary.get("chat_ids", []))
        if overlap > 0:
            summary_copy = dict(summary)
            summary_copy["_score"] = score
            scored.append(summary_copy)
    relevant = sorted(scored, key=lambda item: (item["_score"], item.get("created_at", "")), reverse=True)[:limit]
    return [{key: value for key, value in item.items() if key != "_score"} for item in relevant]


def get_unsummarized_chat_history(batch_size: int = 8) -> List[Dict[str, object]]:
    store = _read_store()
    summarized_ids: Set[int] = set()
    for summary in store.get("conversation_summaries", []):
        summarized_ids.update(int(chat_id) for chat_id in summary.get("chat_ids", []))

    unsummarized = [
        item
        for item in store.get("chat_memory", [])
        if int(item.get("id", -1)) not in summarized_ids
    ]
    return unsummarized[-batch_size:]


def cleanup_memory_store(max_memories: int = 60) -> None:
    store = _read_store()
    memories = [
        item
        for item in store.get("long_term_memory", [])
        if not item.get("archived", False)
    ]
    memories.sort(
        key=lambda item: (
            int(item.get("importance", 3)),
            item.get("last_used_at") or "",
            item.get("updated_at") or "",
        ),
        reverse=True,
    )
    archived_ids = {int(item["id"]) for item in memories[max_memories:]}
    changed = False
    for memory in store.get("long_term_memory", []):
        if int(memory.get("id", -1)) in archived_ids:
            memory["archived"] = True
            changed = True
    if changed:
        _write_store(store)
