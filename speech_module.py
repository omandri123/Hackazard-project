

# FILE: speech_to_text.py

import speech_recognition as sr
from datetime import datetime
import json
import threading

# Thread-safe stop flag
stop_event = threading.Event()
recognized_data = []

def stop_audio_capture():
    stop_event.set()

def run_speech_to_text():
    global recognized_data
    stop_event.clear()
    recognized_data = []

    recognizer = sr.Recognizer()

    print("🎙️ Adjusting for ambient noise...")

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print("🎧 Listening started... (Waiting for user input or STOP button)")

            while not stop_event.is_set():
                try:
                    print("👂 Listening...")
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                    recognized_text = recognizer.recognize_google(audio)
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    recognized_data.append({"timestamp": timestamp, "text": recognized_text})
                    print(f"🗣️ {timestamp} - {recognized_text}")
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    print("❌ Couldn't understand the audio.")
                except sr.RequestError:
                    print("🚫 Issue with the speech recognition service.")
                except Exception as e:
                    print("⚠️ Unexpected error:", e)
    except Exception as mic_error:
        print("🎤 Microphone error:", mic_error)

    # Save the transcript to JSON
    with open("speech_transcript_output.json", "w") as f:
        json.dump(recognized_data, f, indent=2)

    print("✅ Speech data saved to speech_transcript_output.json")
    print("\nPress Enter : For Generating the Response  ")

def get_transcript():
    return recognized_data
