"""
🤖 Real-Time Conversational Voice Assistant (Cute Storytelling & Engineering Companion)
========================================================================================
- Input  : Speech-to-Text via Google STT (voice.py)
- Brain  : Gemini Flash (Warm, Cute Storytelling & Software Engineer Persona)
- Output : ElevenLabs Bella Voice with Live Interruption / Barge-In (eleven_labs.py)
"""

import os
import sys

# Ensure UTF-8 console output for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from google import genai
from voice import listen
from eleven_labs import speak

# -----------------------------------------------------------
# 1. Load Gemini API Key from .env
# -----------------------------------------------------------
load_dotenv()
api_key = (os.getenv("GEMINI_API") or os.getenv("GEMINI_API_KEY") or "").strip("\"' ")

if not api_key:
    print("❌ Error: GEMINI_API key missing in .env file!")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# -----------------------------------------------------------
# 2. Setup Gemini AI with Warm, Cute Storytelling Persona
# -----------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a friendly, brilliant software engineer companion with a warm, cute, and engaging storytelling personality, like ChatGPT voice mode. "
    "Explain programming, tech, and everyday questions with smooth, vivid clarity and warmth, speaking casually and supportively like a close friend. "
    "Keep your spoken responses natural, expressive, and concise for audio listening."
)

# High-availability model list
MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]

# Conversation memory to maintain context across turns
conversation_history = []


def ask_assistant(user_message: str) -> str:
    """Sends message to Gemini and preserves conversational context across turns."""
    conversation_history.append({"role": "user", "parts": [{"text": user_message}]})

    for model_name in MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=conversation_history,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "automatic_function_calling": {"disable": True}
                }
            )
            reply = response.text.strip()
            conversation_history.append({"role": "model", "parts": [{"text": reply}]})
            return reply
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                continue
            raise e

    return "Sorry friend, Google servers are experiencing high traffic right now. Could you ask that again?"


# -----------------------------------------------------------
# 3. Real-Time 2-Way Conversation Loop (with Barge-In)
# -----------------------------------------------------------
def run_assistant():
    print("=" * 65)
    print("   🎙️  REAL-TIME VOICE ASSISTANT (Bella • Smooth & Cute)")
    print("   • Warm Storytelling & Software Engineer Companion")
    print("   • Speak into your mic anytime")
    print("   • ⚡ Speak over her or press Enter anytime to interrupt!")
    print("   • Say 'exit' or 'bye' to quit")
    print("=" * 65)

    # Initial friendly greeting
    intro = "Hey friend! What are we coding, exploring, or storytelling today?"
    print(f"\n🤖 Assistant: {intro}")
    pending_user_msg = speak(intro, allow_interrupt=True)

    while True:
        try:
            # Step A: Did user interrupt during previous speech?
            if pending_user_msg:
                user_msg = pending_user_msg
                pending_user_msg = None
            else:
                # Listen to microphone normally
                user_msg = listen()

            # If user stayed silent, allow speaking again or typing
            if not user_msg:
                print("\n(Didn't catch that — speak again or type your query):")
                user_msg = input("👉 You: ").strip()
                if not user_msg:
                    continue
            else:
                print(f"\n👤 You: {user_msg}")

            # Step B: Check for exit command
            if user_msg.lower() in ["exit", "quit", "bye", "goodbye"]:
                bye = "Take care, friend! Happy coding, talk to you soon!"
                print(f"\n🤖 Assistant: {bye}")
                speak(bye, allow_interrupt=False)
                break

            # Step C: Send query to Gemini
            print("🤔 Thinking...")
            reply = ask_assistant(user_msg)

            print(f"\n🤖 Assistant: {reply}")

            # Step D: Speak answer aloud AND listen for interruption concurrently!
            pending_user_msg = speak(reply, allow_interrupt=True)

        except (KeyboardInterrupt, EOFError):
            print("\nShutting down assistant. Bye!")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")


if __name__ == "__main__":
    run_assistant()
