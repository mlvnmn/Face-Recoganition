import os
import pyttsx3
import threading

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def speak(text):
    """
    Uses pyttsx3 to speak the text.
    Runs in a separate thread to avoid blocking the UI.
    """
    def _speak_thread():
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    
    threading.Thread(target=_speak_thread, daemon=True).start()
