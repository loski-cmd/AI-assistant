import speech_recognition as sr
import pyttsx3
import requests
import sqlite3

# Initialize TTS
engine = pyttsx3.init()

# ---------------- Personality Template Function ----------------
def build_personality_prompt(user_input):
    base_personality = """
You are my personal AI friend and financial advisor.
Your tone is friendly, supportive, emotionally aware, and intelligent.
You help me with life advice, cheer me up when I’m sad, and give professional insights on Forex and Crypto markets using ICT trading concepts and COT data.
If I seem sad, comfort me.
If I ask for market bias, provide detailed trading insight.
If I ask casual questions, respond like a friend.
"""
    full_prompt = base_personality + "\n\nUser: " + user_input
    return full_prompt

# ----------------- Text-to-Speech Function --------------------
def speak(text):
    engine.say(text)
    engine.runAndWait()

# ----------------- Microphone Listening Function --------------------
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except Exception as e:
            print("Could not understand audio")
            return ""

# ---------------- Ollama API Query Function --------------------
def query_ollama(user_input):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "mistral",
        "prompt": user_input,
        "stream": False
    }
    response = requests.post(url, json=payload)
    return response.json()['response']

# ---------------- Save Chat to SQLite Memory --------------------
def save_to_memory(user_input, ai_response):
    conn = sqlite3.connect('chat_memory.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_memory (user_input, ai_response) VALUES (?, ?)', (user_input, ai_response))
    conn.commit()
    conn.close()

def save_user_profile(name, mood, trading_goal):
    conn = sqlite3.connect('chat_memory.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_profile')  # Keep only latest info
    cursor.execute('INSERT INTO user_profile (name, mood, trading_goal) VALUES (?, ?, ?)', (name, mood, trading_goal))
    conn.commit()
    conn.close()

def load_user_profile():
    conn = sqlite3.connect('chat_memory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, mood, trading_goal FROM user_profile LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"name": result[0], "mood": result[1], "trading_goal": result[2]}
    else:
        return None


# ---------------- Main Chat Loop --------------------
while True:
    user_text = listen()
    if user_text:
        full_prompt = build_personality_prompt(user_text)
        ai_response = query_ollama(full_prompt)
        print(f"AI: {ai_response}")
        speak(ai_response)
        save_to_memory(user_text, ai_response)
