import subprocess

import speech_recognition as sr

from config import PREFERRED_VOICE_HINTS, VOICE_RATE, VOICE_VOLUME


def _escape_powershell_text(text: str) -> str:
    return text.replace("'", "''")


def speak(text: str) -> None:
    safe_text = _escape_powershell_text(text)
    voice_hints = ",".join(PREFERRED_VOICE_HINTS)
    command = (
        "Add-Type -AssemblyName System.Speech; "
        "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$voiceHints = '{_escape_powershell_text(voice_hints)}'.Split(','); "
        "$preferredVoice = $speaker.GetInstalledVoices() | "
        "ForEach-Object { $_.VoiceInfo.Name } | "
        "Where-Object { $voiceName = $_; $voiceHints | Where-Object { $voiceName -like ('*' + $_ + '*') } } | "
        "Select-Object -First 1; "
        "if ($preferredVoice) { $speaker.SelectVoice($preferredVoice) }; "
        f"$speaker.Rate = {VOICE_RATE}; "
        f"$speaker.Volume = {VOICE_VOLUME}; "
        f"$speaker.Speak('{safe_text}')"
    )

    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        error_text = completed.stderr.strip() or completed.stdout.strip() or "Unknown TTS error."
        raise RuntimeError(f"Voice output failed: {error_text}")


def test_voice_output() -> str:
    sample_text = "Hello, I am Ava. My voice is ready."
    speak(sample_text)
    return sample_text


def listen(
    timeout: float | None = None,
    phrase_time_limit: float | None = None,
    pause_threshold: float = 0.8,
    non_speaking_duration: float = 0.5,
) -> str:
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = pause_threshold
    recognizer.non_speaking_duration = non_speaking_duration

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
            )
        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return ""

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""
    except sr.RequestError as exc:
        print(f"Speech recognition service error: {exc}")
        return ""
