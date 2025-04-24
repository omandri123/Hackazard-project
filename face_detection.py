

# FILE: face_detection.py

import cv2
from deepface import DeepFace
from collections import defaultdict
import time
import json
import threading

# Thread-safe stop flag
stop_event = threading.Event()

def stop_face_analysis():
    stop_event.set()

def run_face_expression_analysis():
    stop_event.clear()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("🚫 Error: Could not open webcam.")
        return

    emotion_duration = defaultdict(float)
    last_emotion = None
    last_time = time.time()

    print("📸 Camera started. Running emotion analysis...")

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to grab frame.")
            break

        try:
            analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            emotion = analysis[0]['dominant_emotion']
        except Exception as e:
            print("⚠️ Face not detected:", e)
            continue

        current_time = time.time()
        duration = current_time - last_time

        if last_emotion:
            emotion_duration[last_emotion] += duration

        last_emotion = emotion
        last_time = current_time

        # Optional UI feedback
        cv2.putText(frame, f"Emotion: {emotion}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Interview Emotion Tracker - Press STOP to exit', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🛑 Manual stop triggered.")
            break

    cap.release()
    cv2.destroyAllWindows()

    # Final update for last emotion
    if last_emotion:
        emotion_duration[last_emotion] += time.time() - last_time

    # Round durations
    emotion_duration = {k: round(v, 2) for k, v in emotion_duration.items()}

    # Save to JSON
    with open("face_expression_output.json", "w") as f:
        json.dump(emotion_duration, f)

    print("✅ Emotion data saved to face_expression_output.json")