"""
Voice Output (Text-to-Speech with Real-Time Interruption / Barge-in)
Uses ElevenLabs 24kHz PCM streaming for instant playback and instant cutoff.
Voice: Bella (EXAVITQu4vr4xnSDxMaL) - Smooth, cute, expressive storytelling tone.
"""

import os
import sys
import time

# Windows UTF-8 encoding support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Windows non-blocking keyboard check
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

import numpy as np
import sounddevice as sd
import speech_recognition as sr
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Step 1: Load credentials from .env
load_dotenv()

ELEVENLABS_KEY = (os.getenv("ELEVENLABS_API_KEY") or "").strip("\"' ")

# Bella: Soft, cute, sweet, storytelling tone like ChatGPT voice mode
VOICE_ID = (
    os.getenv("ELEVENLABS_VOICE_ID_BELLA")
    or os.getenv("ELEVENLABS_VOICE_ID_JESSICA")
    or os.getenv("ELEVENLABS_VOICE_ID_ALICE")
    or "EXAVITQu4vr4xnSDxMaL"
).strip("\"' ")

# Create ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_KEY) if ELEVENLABS_KEY else None
recognizer = sr.Recognizer()


def speak(text: str, allow_interrupt: bool = True) -> str | None:
    """
    Speaks text aloud using Bella's smooth, cute, storytelling voice.
    If you speak or press Enter while she is talking, she stops IMMEDIATELY!
    """
    if not text or not text.strip():
        return None

    print("\n🔊 Speaking... (Speak into mic or press Enter anytime to interrupt)")

    if not client:
        print("⚠️ ElevenLabs client not initialized.")
        return None

    # Step 1: Request high-speed raw PCM audio from ElevenLabs (Turbo v2.5)
    # Using stability=0.45 & similarity_boost=0.85 for cute, expressive cadence
    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=text,
            model_id="eleven_turbo_v2_5",
            output_format="pcm_24000",
            voice_settings={
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.25
            }
        )
        raw_pcm = b"".join([c for c in audio_stream if c])
        audio_array = np.frombuffer(raw_pcm, dtype=np.int16)
    except Exception as e:
        print(f"⚠️ ElevenLabs error: {e}")
        return None

    # If interruption is disabled, play normally
    if not allow_interrupt:
        sd.play(audio_array, samplerate=24000)
        sd.wait()
        return None

    # Step 2: Play audio and monitor microphone & keyboard simultaneously
    sd.play(audio_array, samplerate=24000)

    mic_sample_rate = 16000
    chunk_size = 1600  # 100ms
    user_frames = []
    interrupted = False
    silent_chunks = 0
    start_time = time.time()

    # Sensitive threshold for normal conversational voice
    interrupt_threshold = 480

    try:
        with sd.InputStream(samplerate=mic_sample_rate, channels=1, dtype="int16") as stream:
            # While audio is playing, listen for voice or keypress
            while sd.get_stream() and sd.get_stream().active:
                chunk, _ = stream.read(chunk_size)

                # Check if user pressed a key to interrupt
                if HAS_MSVCRT and msvcrt.kbhit():
                    msvcrt.getch()  # consume keypress
                    sd.stop()
                    print("\n🛑 [Key pressed!] Interrupted. Listening to you...")
                    interrupted = True
                    break

                # Skip first 0.2s to prevent initial room click
                if time.time() - start_time < 0.2:
                    continue

                energy = np.abs(chunk).mean()

                # If your voice energy is detected, interrupt immediately!
                if energy > interrupt_threshold:
                    sd.stop()
                    print("\n🛑 [Voice detected!] Interrupted. Listening to you...")
                    interrupted = True
                    user_frames.append(chunk.tobytes())
                    break

            # If user interrupted, record their question until they finish speaking
            if interrupted:
                for _ in range(120):  # Maximum 12 seconds
                    chunk, _ = stream.read(chunk_size)
                    user_frames.append(chunk.tobytes())
                    energy = np.abs(chunk).mean()

                    if energy < 350:
                        silent_chunks += 1
                        if silent_chunks >= 12:  # 1.2s silence
                            break
                    else:
                        silent_chunks = 0

                print("🔄 Processing your interruption...")
                if user_frames:
                    audio_data = sr.AudioData(b"".join(user_frames), mic_sample_rate, 2)
                    try:
                        interrupted_text = recognizer.recognize_google(audio_data).strip()
                        if interrupted_text:
                            print(f"👤 You: {interrupted_text}")
                            return interrupted_text
                    except Exception:
                        pass

                # If no speech was captured from the interruption, let the user speak
                return None

    except Exception as e:
        sd.stop()
        print(f"Barge-in error: {e}")

    # Wait for normal playback to finish if no interruption
    sd.wait()
    return None


if __name__ == "__main__":
    speak("Hello there! I am Bella. I can tell you stories, explain code, and we can chat about anything you like!")
