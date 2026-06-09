from config import ASSISTANT_NAME, LONG_TERM_MEMORY_LIMIT, PREFERENCE_LIMIT, RECENT_HISTORY_LIMIT
from database import (
    get_relevant_conversation_summaries,
    get_relevant_long_term_memories,
    get_recent_chat_history,
    get_user_preferences,
    init_database,
    load_user_profile,
    save_chat_memory,
)
from llm_service import query_ollama
from memory_extractor import extract_and_store_memories
from memory_manager import maintain_memory_system
from mode_router import detect_conversation_mode
from personality import build_personality_prompt
from speech_service import listen, speak


def generate_response(user_text: str) -> str:
    user_profile = load_user_profile()
    recent_history = get_recent_chat_history(limit=RECENT_HISTORY_LIMIT)
    long_term_memories = get_relevant_long_term_memories(user_text, limit=LONG_TERM_MEMORY_LIMIT)
    conversation_summaries = get_relevant_conversation_summaries(user_text, limit=2)
    preferences = get_user_preferences(limit=PREFERENCE_LIMIT)
    conversation_mode = detect_conversation_mode(user_text)
    prompt = build_personality_prompt(
        user_input=user_text,
        conversation_mode=conversation_mode,
        user_profile=user_profile,
        recent_history=recent_history,
        long_term_memories=long_term_memories,
        preferences=preferences,
        conversation_summaries=conversation_summaries,
    )
    return query_ollama(prompt)


def chat_once(user_text: str, speak_response: bool = False) -> str:
    extract_and_store_memories(user_text)
    conversation_mode = detect_conversation_mode(user_text)
    ai_response = generate_response(user_text)
    save_chat_memory(user_text, ai_response, mode=conversation_mode)
    maintain_memory_system()

    if speak_response:
        try:
            speak(ai_response)
        except Exception as exc:
            print(f"Voice output warning: {exc}")

    return ai_response


def run_voice_assistant() -> None:
    init_database()
    print(f"{ASSISTANT_NAME} is ready. Press Ctrl+C to stop.")

    while True:
        user_text = listen()
        if not user_text:
            continue

        try:
            ai_response = chat_once(user_text, speak_response=True)
            print(f"{ASSISTANT_NAME}: {ai_response}")
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"I ran into an issue: {exc}")
            try:
                speak("I ran into an issue. Please check the terminal and try again.")
            except Exception:
                pass


if __name__ == "__main__":
    try:
        run_voice_assistant()
    except KeyboardInterrupt:
        print("\nAssistant stopped.")
