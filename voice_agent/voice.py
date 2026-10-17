import numpy as np
import speech_recognition as sr
import sounddevice as sd

# Initialize Google speech recognizer
recognizer = sr.Recognizer()


def listen(prompt_msg: str = "🎤 Listening... (Speak now)") -> str:
    """Listens to microphone and turns speech into text."""
    print(f"\n{prompt_msg}")

    # Step 1: Try recording using standard speech_recognition microphone
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)  # Filter background noise
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)
            print("🔄 Processing speech...")
            return recognizer.recognize_google(audio).strip()  # Convert speech to text
    except Exception:
        pass  # If PyAudio is missing, use sounddevice below

    # Step 2: Fallback recorder using sounddevice (works on all Windows PCs)
    sample_rate = 16000
    chunk_size = 1600  # 100 milliseconds per chunk
    frames = []
    silent_chunks = 0
    speaking = False

    try:
        # Open microphone stream
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
            for _ in range(120):  # Maximum 12 seconds of recording
                chunk, _ = stream.read(chunk_size)
                frames.append(chunk.tobytes())

                # Check if user started speaking (volume louder than threshold)
                if np.abs(chunk).mean() > 350:
                    speaking = True
                    silent_chunks = 0
                elif speaking:
                    silent_chunks += 1
                    # Stop recording after 1.2 seconds of silence
                    if silent_chunks >= 12:
                        break

        # If user didn't speak anything, return empty text
        if not speaking:
            return ""

        print("🔄 Processing speech...")
        # Pack raw audio bytes into Google speech recognition format
        audio_data = sr.AudioData(b"".join(frames), sample_rate, 2)
        return recognizer.recognize_google(audio_data).strip()

    except (sr.UnknownValueError, sr.WaitTimeoutError):
        return ""  # Silence or unrecognized words
    except Exception as e:
        print(f"⚠️ Speech Error: {e}")
        return ""


if __name__ == "__main__":
    text = listen()
    print(f"You said: '{text}'")