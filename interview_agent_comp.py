# Full updated main.py based on your request

import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import threading
import time
import requests
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import pyttsx3
from datetime import datetime
import os

from face_detection import run_face_expression_analysis, stop_face_analysis
from speech_module import run_speech_to_text, stop_audio_capture, get_transcript

GROQ_API_KEY = "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"
GROQ_MODEL = "llama3-70b-8192"

engine = pyttsx3.init()
stop_flag = False
all_responses = []


def speak(text):
    engine.say(text)
    engine.runAndWait()


def send_to_groq(prompt_content):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt_content}]
        }
    )
    try:
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return result.get("error", {}).get("message", "Unknown error")
    except Exception as e:
        return f"Error parsing response: {str(e)}"


def generate_pie_chart(emotion_data, filename="emotion_pie_chart.png"):
    labels = list(emotion_data.keys())
    sizes = list(emotion_data.values())
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title("Emotion Distribution During Interview")
    plt.savefig(filename)
    plt.close()


def create_pdf_report(feedback_text, username,criteria,purpose = "", filename="interview_feedback_report.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)

    # Title
    c.drawString(30, height - 40, f"{username}'s Interview Feedback Report")

    # Candidate Details
    c.setFont("Helvetica", 12)
    y = height - 70
    c.drawString(30, y, f"First Name: {username}")
    y -= 20
    c.drawString(30, y, f"Purpose: {purpose}")
    y -= 20
    c.drawString(30, y, f"Criteria: {criteria}")
    y -= 30

    # Insert the chart
    try:
        c.drawImage("emotion_pie_chart.png", 30, y - 280, width=500, height=300)
        y -= 310
    except:
        pass

    # Feedback Text: well-spaced paragraphs
    paragraphs = feedback_text.strip().split('\n\n')  # Split into paragraphs

    for para in paragraphs:
        wrapped_lines = simpleSplit(para.strip(), "Helvetica", 12, width - 60)
        for line in wrapped_lines:
            c.drawString(30, y, line)
            y -= 15
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height - 40
    y -= 10  # Extra space between paragraphs

    c.save()


def show_stop_window():
    def press_stop():
        global stop_flag
        stop_flag = True
        stop_face_analysis()
        stop_audio_capture()
        win.quit()

    win = tk.Tk()
    win.title("Stop Interview")
    win.geometry("250x100")
    tk.Label(win, text="Press to stop the session early", font=("Arial", 10)).pack(pady=10)
    tk.Button(win, text="STOP", command=press_stop, bg="red", fg="white", font=("Arial", 12)).pack()
    return win


def start_training(root):
    global stop_flag, all_responses
    stop_flag = False
    all_responses = []

    username = simpledialog.askstring("Training", "Enter your name:")
    purpose = simpledialog.askstring("Training", "What are you preparing this interview for?")
    criteria = simpledialog.askstring("Training", "Enter the judgement criteria:")
    if not username or not purpose or not criteria:
        messagebox.showerror("Error", "Name, Purpose and Criteria are required.")
        return

    prompt = f'''Imagine you're a professional interview coach helping a candidate prepare for a 
    high-stakes interview. Your goal is to generate 5 unique and insightful interview questions 
    that not only evaluate the candidate's skills but also their personality, problem-solving ability, 
    and cultural fit. Tailor these questions specifically for the purpose of {purpose}, ensuring that they 
    are engaging, thought-provoking, and aligned with the roles requirements. 
    NOTE : No need to write anything like "Here are 5 unique and insightful interview questions" above the questions, just start with askinng the first question '''

    questions_response = send_to_groq(prompt)
    questions = [q.strip("1234567890). ").strip() for q in questions_response.split("\n") if q.strip()]

    if not questions:
        messagebox.showerror("Error", "Failed to retrieve questions from Groq.")
        return



    stop_window = show_stop_window()
    stop_window.update()

    for idx, question in enumerate(questions[:5], 1):
        if stop_flag:
            break
        
        print(f"Question {idx}: {question}")
        speak(f"Question {idx}: {question}")
        

        open("face_expression_output.json", "w").write("{}")
        open("speech_transcript_output.json", "w").write("[]")

        face_thread = threading.Thread(target=run_face_expression_analysis)
        audio_thread = threading.Thread(target=run_speech_to_text)
        face_thread.start()
        audio_thread.start()

        if stop_flag:
            break

        speak("Press Enter in the terminal, when your answer is finished.")
        try:
            input("👉 Press ENTER here in terminal after you're done answering...")
        except:
            pass

        stop_face_analysis()
        stop_audio_capture()
        face_thread.join()
        audio_thread.join()

        try:
            with open("face_expression_output.json") as f:
                face_data = json.load(f)
            speech_data = get_transcript()
        except Exception as e:
            face_data, speech_data = {}, "No data"

        all_responses.append({
            "question": question,
            "face_analysis": face_data,
            "speech_transcript": speech_data
        })

        
        
    if stop_window.winfo_exists():
        stop_window.quit()

    if all_responses:
        summary_prompt = (
            f"You are a professional interview evaluator. Evaluate the following interview with this judgement criteria: {criteria}. "
            f"Give detailed feedback for each question, analyze emotional and speech data, rank the candidate, and give a motivational quote.\n\n"
            f"Candidate Name: {username}\n"
            f"Purpose: {purpose}\n"
            f"Data: {json.dumps(all_responses, indent=2)}"
        )
        final_feedback = send_to_groq(summary_prompt)

        with open(f"{username}_training_feedback.txt", "w") as f:
            print(final_feedback)
            f.write(final_feedback)
        generate_pie_chart(all_responses[-1]["face_analysis"])
        create_pdf_report(final_feedback,username , criteria, purpose , f"{username}_training_report.pdf")
        messagebox.showinfo("Training Complete", f"Feedback saved as {username}_training_report.pdf")


def run_interview_agent(root):
    global stop_flag, all_responses
    stop_flag = False
    all_responses = []

    username = simpledialog.askstring("Interview Agent", "Enter your name:")
    criteria = simpledialog.askstring("Interview Agent", "Enter the judgement criteria:")

    messagebox.showinfo("Agent Mode", "Interview will begin. Press STOP to end anytime.")
    stop_window = show_stop_window()
    stop_window.update()

    face_thread = threading.Thread(target=run_face_expression_analysis)
    audio_thread = threading.Thread(target=run_speech_to_text)
    face_thread.start()
    audio_thread.start()

    stop_window.mainloop()

    stop_face_analysis()
    stop_audio_capture()
    face_thread.join()
    audio_thread.join()

    try:
        with open("face_expression_output.json") as f:
            face_data = json.load(f)
        speech_data = get_transcript()

        all_responses = [{
            "face_analysis": face_data,
            "speech_analysis": speech_data
        }]

        combined_prompt = (
            f"You are a professional interview evaluator. Evaluate the candidate {username} based on this judgement criteria: {criteria}.\n"
            f"Analyze the facial expressions and speech, give a score out of 100, letter grade, detailed feedback, and a motivational quote:\n\n"
            f"{json.dumps(all_responses, indent=2)}"
        )
        feedback = send_to_groq(combined_prompt)

        with open("groq_final_feedback.txt", "w") as f:
            f.write(feedback)
        generate_pie_chart(face_data)
        create_pdf_report(feedback,username, criteria,'No purpose Specified', f"{username}_agent_report.pdf")
        messagebox.showinfo("Agent Feedback", f"Report saved as {username}_agent_report.pdf")
    except Exception as e:
        print("Error while processing agent feedback:", str(e))


def main_menu():
    root = tk.Tk()
    root.title("Interview System")
    root.geometry("400x250")

    tk.Label(root, text="Select Mode", font=("Arial", 16)).pack(pady=20)
    tk.Button(root, text="Start Training Mode", font=("Arial", 14), width=25,
              command=lambda: start_training(root)).pack(pady=10)
    tk.Button(root, text="Run Interview Agent", font=("Arial", 14), width=25,
              command=lambda: run_interview_agent(root)).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main_menu()
