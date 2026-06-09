from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MEMORY_STORE_PATH = BASE_DIR / "assistant_memory.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"
OLLAMA_TEMPERATURE = 0.35
OLLAMA_TOP_P = 0.9

ASSISTANT_NAME = "Ava"
ASSISTANT_IDENTITY = "A warm, feminine, emotionally intelligent AI companion and market-aware guide."
RECENT_HISTORY_LIMIT = 5
LONG_TERM_MEMORY_LIMIT = 5
PREFERENCE_LIMIT = 5
PREFERRED_VOICE_HINTS = ["Zira", "Female"]
VOICE_RATE = 1
VOICE_VOLUME = 100
