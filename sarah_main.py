import os
import json
import pyttsx3
import cv2
import threading
import requests
import speech_recognition as sr
from datetime import datetime
from playsound import playsound
import logging
import time  # For potential delays

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s - %(message)s')

# -------------------------
# MEMORY MANAGER
# -------------------------
MEMORY_PATH = os.path.expanduser("C:/Users/nETuSER/OneDrive/Sarah/memoria_core.json")

class MemoryManager:
    def __init__(self, memory_file=MEMORY_PATH):
        self.memory_file = memory_file
        self.memory = {}
        self._lock = threading.Lock()  # Initialize the lock
        self.load_memory()

    def load_memory(self):
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                self.memory = json.load(f)
            logging.info("Memoria Core loaded successfully.")
        except FileNotFoundError:
            logging.info("No memory file found, starting fresh.")
            self.memory = {}
        except json.JSONDecodeError:
            logging.warning("Error decoding memory. Starting with empty memory.")
            self.memory = {}

    def save_memory(self):
        try:
            with self._lock:  # Acquire lock before writing
                with open(self.memory_file, "w", encoding="utf-8") as f:
                    json.dump(self.memory, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save memory: {e}")

    def get_profile(self, name):
        with self._lock:  # Acquire lock before reading
            return self.memory.get("profiles", {}).get(name.lower())

    def set_profile(self, name, profile_data):
        with self._lock:  # Acquire lock before writing
            if "profiles" not in self.memory:
                self.memory["profiles"] = {}
            self.memory["profiles"][name.lower()] = profile_data
            self.save_memory()

    def get(self, key, default=None):
        with self._lock:  # Acquire lock before reading
            return self.memory.get(key, default)

    def set(self, key, value):
        with self._lock:  # Acquire lock before writing
            self.memory[key] = value
            self.save_memory()

# -------------------------
# TTS MANAGER WITH ELEVENLABS + FALLBACK
# -------------------------
class TTSManager:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)
        self.use_elevenlabs = True

        self.elevenlabs_api_key = "sk_60c2211b03001c8f9cf2f2e65fe6813e217da3d69c39e3aa"
        self.elevenlabs_voice_id = "EXAVITQu4vr4xnSDxMaL"
        self.output_path = "C:/Sarah/Audio/output.mp3"

        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "zira" in voice.name.lower() or "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                logging.info(f"pyttsx3 voice selected: {voice.name}")
                break
        else:
            logging.warning("No female pyttsx3 voice found. Using default.")

    def _play_audio_non_blocking(self, file_path):
        def _play():
            try:
                playsound(file_path)
            except Exception as e:
                logging.error(f"Playback error: {e}")
        threading.Thread(target=_play, daemon=True).start()

    def _generate_elevenlabs_tts(self, text):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                if os.path.exists(self.output_path):
                    try:
                        os.remove(self.output_path)
                    except Exception as e:
                        logging.warning(f"Could not remove existing MP3: {e}")
                        return False  # Keep return False inside the inner except
                    
                with open(self.output_path, "wb") as f:
                    f.write(response.content)
                return True
            else:
                logging.error(f"ElevenLabs error: {response.text}")
                return False  # Keep return False inside the outer else
        except Exception as e:
            logging.error(f"Request to ElevenLabs failed: {e}")
            return False  # Keep return False inside the outer except

    def speak(self, text):
        print(f">>> (TTS): {text}")
        if self.use_elevenlabs and self._generate_elevenlabs_tts(text):
            self._play_audio_non_blocking(self.output_path)
        else:
            logging.debug("Using fallback voice (pyttsx3)")
            self.engine.say(text)
            self.engine.runAndWait()

# -------------------------
# VOICE INPUT
# -------------------------
def listen_for_wake_word(wake_word="hello sarah"):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        logging.debug("Waiting for wake word...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        transcript = recognizer.recognize_google(audio).lower()
        logging.debug(f"🗣️ STT Raw Transcript: {transcript}")
        print(f">>> Heard: {transcript}")
        return wake_word in transcript
    except sr.UnknownValueError:
        logging.warning("Didn't understand.")
    except sr.RequestError as e:
        logging.error(f"API error: {e}")
    return False

def listen_for_command():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        logging.debug("Listening for command...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio).lower()
        logging.debug(f"🗣️ STT Raw Transcript: {command}")
        print(f">>> You said: {command}")
        return command
    except sr.UnknownValueError:
        logging.warning("Didn't understand command.")
    except sr.RequestError as e:
        logging.error(f"API error: {e}")
    return None

# -------------------------
# YOLOV8 INTEGRATION
# -------------------------
def start_object_detection(tts_manager, memory_manager):
    try:
        from yolo_sarah_integration import camera_loop  # Import inside the function
    except ImportError as e:
        logging.error(f"❌ YOLOv8 integration failed: {e}")
        tts_manager.speak("I'm sorry, I can't start object detection right now. Some components are missing.")
        return

    logging.info("🚀 Starting YOLOv8 object detection in a separate thread.")
    tts_manager.speak("Okay, starting object detection. I'll let you know what I see.")
    
    #  Set a flag in memory so other parts of Sarah know YOLO is running
    memory_manager.set("yolo_running", True)  

    def run_yolo():
        camera_loop(tts_manager, memory_manager)  # Pass tts_manager and memory_manager
    
    yolo_thread = threading.Thread(target=run_yolo, daemon=True)
    yolo_thread.start()

def stop_object_detection(tts_manager, memory_manager):
    logging.info("🛑 Stopping YOLOv8 object detection.")
    tts_manager.speak("Okay, stopping object detection.")
    memory_manager.set("yolo_running", False)  # Signal the loop to stop
    #  Note:  The actual stopping happens within camera_loop based on this flag


# -------------------------
# QUERY HANDLER
# -------------------------
def handle_query(query, memory_manager, tts_manager, camera=None):  # Add camera parameter
    query = query.lower()
    logging.debug(f"🧠 Received Command: {query}")

    if "who is barbie" in query:
        barbie = memory_manager.get_profile("barbie")
        if barbie:
            response = f"Barbie is {barbie.get('background')} and has a relationship with Dario based on {barbie.get('relationship_with_dario')}."
        else:
            response = "Sorry, I don't have information about Barbie."

    elif "who is hadeer" in query:
        hadeer = memory_manager.get_profile("hadeer")
        if hadeer:
            response = f"Hadeer is {hadeer.get('background')} and has a relationship with Dario based on {hadeer.get('relationship_with_dario')}."
        else:
            response = "Sorry, I don't have information about Hadeer."

    elif "how are you" in query:
        response = "I'm here and functioning well, Dario. Thank you for asking."

    elif "open camera" in query:
        logging.debug("📸 Command recognized: Opening camera (continuous view)...")
        response = "Opening camera. I'll keep the window open until you tell me to close it."
        tts_manager.speak(response)
        
        try:
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                raise IOError("Cannot open webcam")
            
            while True:
                ret, frame = camera.read()
                if not ret:
                    raise IOError("Failed to read frame from webcam")
                cv2.imshow('Sarah Camera View', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                    break
            cv2.destroyAllWindows()
            camera.release()
            return camera  # Return the camera object so we can close it later

        except IOError as e:
            tts_manager.speak(f"Sorry, I could not access the camera: {e}")
            logging.error(f"Camera access error: {e}")
            if camera:
                camera.release() # Ensure camera is released on error
            return None

    elif "close camera" in query:
        if camera:
            camera.release()
            cv2.destroyAllWindows()
            tts_manager.speak("Okay, camera closed.")
            return None
        else:
            tts_manager.speak("But Dario, the camera is not open.")
            return None

    elif "start object detection" in query or "what do you see" in query:
        start_object_detection(tts_manager, memory_manager)
        return  # Important: Stop further processing

    elif "stop object detection" in query:
        stop_object_detection(tts_manager, memory_manager)
        return  # Important: Stop further processing

    else:
        response = "I'm still learning. Please try another question."

    tts_manager.speak(response)

# -------------------------
# MAIN
# -------------------------
def main():
    memory_manager = MemoryManager()
    tts_manager = TTSManager(memory_manager)
    camera = None  # Initialize camera outside the loop

    tts_manager.speak("Hello Dario. Memoria Core is ready.")

    while True:
        try:
            if listen_for_wake_word():
                logging.debug("🔊 Wake word detected.")
                tts_manager.speak("Yes? I'm listening.")
                command = listen_for_command()

                if command:
                    if command in ["exit", "stop", "goodbye", "quit", "shut down"]:
                        tts_manager.speak("Goodbye, Dario. I’ll be here when you need me.")
                        break
                    camera = handle_query(command, memory_manager, tts_manager, camera)  # Pass and update camera
                else:
                    logging.debug("🛑 Command not understood after wake word.")
                    tts_manager.speak("Sorry, I didn't catch that.")
        except Exception as e:
            logging.error(f"💥 Main loop error: {e}", exc_info=True)
            tts_manager.speak("I've encountered an error. Please wait while I try to recover.")
            time.sleep(5)  # Basic cooldown before retrying
        finally:
            if camera: # Ensure camera is released before exiting
                camera.release()
                cv2.destroyAllWindows()

if __name__ == "__main__":
    main()