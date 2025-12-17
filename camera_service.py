import cv2
import face_recognition
import pickle
import threading
import time
import os
from PIL import Image, ImageTk

class CameraService:
    def __init__(self, encodings_file="encodings.pickle", detection_callback=None):
        self.video_capture = None
        self.is_running = False
        self.mode = "attendance" # 'attendance' or 'capture'
        self.encodings_file = encodings_file
        self.detection_callback = detection_callback
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_encodings()

        self.current_frame = None
        self.lock = threading.Lock()
        
        # Capture session variables
        self.capture_session_active = False
        self.capture_count = 0
        self.capture_target = 20
        self.capture_folder = ""
        self.capture_callback = None

    def load_encodings(self):
        if os.path.exists(self.encodings_file):
            print("[INFO] Loading encodings...")
            data = pickle.loads(open(self.encodings_file, "rb").read())
            self.known_face_encodings = data["encodings"]
            self.known_face_names = data["names"]
        else:
            print("[WARN] No encodings file found.")
            self.known_face_encodings = []
            self.known_face_names = []

    def start(self):
        if self.is_running:
            return
        self.video_capture = cv2.VideoCapture(0)
        self.is_running = True
        threading.Thread(target=self._video_loop, daemon=True).start()

    def stop(self):
        self.is_running = False
        if self.video_capture:
            self.video_capture.release()

    def set_mode(self, mode):
        self.mode = mode

    def start_capture_session(self, folder_path, callback):
        self.capture_folder = folder_path
        self.capture_count = 0
        self.capture_callback = callback
        self.capture_session_active = True
        self.mode = "capture"

    def _video_loop(self):
        while self.is_running:
            ret, frame = self.video_capture.read()
            if not ret:
                continue

            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)

            if self.mode == "attendance":
                self._process_attendance(frame)
            elif self.mode == "capture":
                self._process_capture(frame)

            # Convert to RGB for tkinter
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            
            with self.lock:
                self.current_frame = img

            time.sleep(0.03) # ~30 FPS

    def _process_attendance(self, frame):
        # Resize for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB) # face_recognition uses RGB

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = self.known_face_names[first_match_index]

            face_names.append(name)
            
            if self.detection_callback:
                self.detection_callback(name)

        # Draw boxes
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

    def _process_capture(self, frame):
        if self.capture_session_active:
            if self.capture_count < self.capture_target:
                # Save frame
                filename = f"{self.capture_folder}/img_{self.capture_count}.jpg"
                cv2.imwrite(filename, frame)
                self.capture_count += 1
                
                # Visual feedback
                cv2.putText(frame, f"Capturing {self.capture_count}/{self.capture_target}", (50, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                time.sleep(0.2) # Delay between captures
            else:
                self.capture_session_active = False
                if self.capture_callback:
                    self.capture_callback()
        else:
            cv2.putText(frame, "Capture Mode", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    def get_frame(self):
        with self.lock:
            return self.current_frame
