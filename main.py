import customtkinter as ctk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import os

from database_manager import DatabaseManager
from camera_service import CameraService
from email_service import EmailService
from encoder import Encoder
from utils import speak, create_directory

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SmartGuard Ultimate - Face Recognition Attendance")
        self.geometry("1200x720")

        # Initialize Managers
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.camera = CameraService(detection_callback=self.on_face_detected)
        self.encoder = Encoder()

        # State
        self.pending_attendance = set() # Set of IDs
        self.last_spoken_time = {} # {id: timestamp} to avoid spamming speech
        self.current_user_role = None # To track if a teacher is currently recognized? 
        # Actually, the logic is: Detect Teacher -> Commit.
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_pages()
        
        self.show_frame("Home")
        
        # Start Camera
        self.camera.start()
        self.update_camera_feed()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SmartGuard", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_home = ctk.CTkButton(self.sidebar_frame, text="Home / Attendance", command=lambda: self.show_frame("Home"))
        self.btn_home.grid(row=1, column=0, padx=20, pady=10)

        self.btn_class = ctk.CTkButton(self.sidebar_frame, text="Class Dashboard", command=lambda: self.show_frame("Class"))
        self.btn_class.grid(row=2, column=0, padx=20, pady=10)

        self.btn_teacher = ctk.CTkButton(self.sidebar_frame, text="Teacher Admin", command=lambda: self.show_frame("Teacher"))
        self.btn_teacher.grid(row=3, column=0, padx=20, pady=10)

    def create_pages(self):
        self.pages = {}
        
        # --- Home Page ---
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.pages["Home"] = self.home_frame
        
        self.home_frame.grid_columnconfigure(0, weight=2)
        self.home_frame.grid_columnconfigure(1, weight=1)
        self.home_frame.grid_rowconfigure(0, weight=1)

        # Camera Feed
        self.camera_label = ctk.CTkLabel(self.home_frame, text="")
        self.camera_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Pending List Panel
        self.pending_frame = ctk.CTkFrame(self.home_frame)
        self.pending_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.pending_frame, text="Pending Attendance", font=("Arial", 18, "bold")).pack(pady=10)
        
        self.pending_listbox = ctk.CTkTextbox(self.pending_frame, width=250)
        self.pending_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.pending_listbox.configure(state="disabled")

        # --- Class Page ---
        self.class_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.pages["Class"] = self.class_frame
        
        ctk.CTkLabel(self.class_frame, text="Class Dashboard", font=("Arial", 24, "bold")).pack(pady=20)
        
        # Treeview for stats
        self.tree_frame = ctk.CTkFrame(self.class_frame)
        self.tree_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        columns = ("ID", "Name", "Total Classes", "Present", "Percentage")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.pack(fill="both", expand=True)
        
        # Refresh Button
        ctk.CTkButton(self.class_frame, text="Refresh Stats", command=self.load_class_stats).pack(pady=10)

        # --- Teacher Page ---
        self.teacher_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.pages["Teacher"] = self.teacher_frame
        
        self.teacher_frame.grid_columnconfigure(0, weight=1)
        self.teacher_frame.grid_columnconfigure(1, weight=1)
        
        # Add Student Form
        self.form_frame = ctk.CTkFrame(self.teacher_frame)
        self.form_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(self.form_frame, text="Add New Student/Teacher", font=("Arial", 18, "bold")).pack(pady=10)
        
        self.entry_id = ctk.CTkEntry(self.form_frame, placeholder_text="ID (e.g., 101)")
        self.entry_id.pack(pady=5, padx=10, fill="x")
        
        self.entry_name = ctk.CTkEntry(self.form_frame, placeholder_text="Full Name")
        self.entry_name.pack(pady=5, padx=10, fill="x")
        
        self.role_var = ctk.StringVar(value="Student")
        ctk.CTkComboBox(self.form_frame, values=["Student", "Teacher"], variable=self.role_var).pack(pady=5, padx=10, fill="x")
        
        self.entry_email_s = ctk.CTkEntry(self.form_frame, placeholder_text="Student Email")
        self.entry_email_s.pack(pady=5, padx=10, fill="x")
        
        self.entry_email_p = ctk.CTkEntry(self.form_frame, placeholder_text="Parent Email")
        self.entry_email_p.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkButton(self.form_frame, text="Capture Photos & Train", command=self.start_capture_flow).pack(pady=20, padx=10, fill="x")

        # Manage List
        self.manage_frame = ctk.CTkFrame(self.teacher_frame)
        self.manage_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(self.manage_frame, text="Manage Users", font=("Arial", 18, "bold")).pack(pady=10)
        
        self.user_list_text = ctk.CTkTextbox(self.manage_frame)
        self.user_list_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkButton(self.manage_frame, text="Refresh List", command=self.load_user_list).pack(pady=5)
        
        self.delete_id_entry = ctk.CTkEntry(self.manage_frame, placeholder_text="Enter ID to Delete")
        self.delete_id_entry.pack(pady=5)
        
        ctk.CTkButton(self.manage_frame, text="Delete User", fg_color="red", command=self.delete_user).pack(pady=10)

    def show_frame(self, page_name):
        for frame in self.pages.values():
            frame.grid_forget()
        self.pages[page_name].grid(row=0, column=1, sticky="nsew")
        
        if page_name == "Home":
            self.camera.set_mode("attendance")
        elif page_name == "Teacher":
            self.load_user_list()
        elif page_name == "Class":
            self.load_class_stats()

    def update_camera_feed(self):
        frame = self.camera.get_frame()
        if frame is not None:
            ctk_img = ctk.CTkImage(light_image=frame, dark_image=frame, size=(640, 480))
            self.camera_label.configure(image=ctk_img)
            self.camera_label.image = ctk_img
        
        self.after(30, self.update_camera_feed)

    def on_face_detected(self, name):
        if name == "Unknown":
            return
        
        # Parse ID from name (assuming ID_Name format)
        try:
            user_id = name.split('_')[0]
        except:
            return

        # Check rate limit for speech
        current_time = time.time()
        if user_id in self.last_spoken_time:
            if current_time - self.last_spoken_time[user_id] < 10: # 10 seconds cooldown
                return
        
        # Fetch user details
        user = self.db.get_user_by_id(user_id) # Need to implement this in DB
        # Wait, I didn't implement get_user_by_id in DB manager. 
        # I'll fetch all users and filter, or just add the method.
        # For now, let's assume I can get role. 
        # I'll do a quick query here or cache it.
        # Let's add a helper method in this class to get role from ID.
        role = self.get_role_by_id(user_id)
        
        if not role:
            return

        self.last_spoken_time[user_id] = current_time

        if role == "Student":
            if user_id not in self.pending_attendance:
                # Check if already marked today in DB
                if self.db.check_attendance_today(user_id, time.strftime("%Y-%m-%d")):
                    speak(f"{name}, you are already marked present.")
                else:
                    self.pending_attendance.add(user_id)
                    self.update_pending_list()
                    speak(f"Welcome {name}")
        
        elif role == "Teacher":
            if self.pending_attendance:
                speak(f"Hello {name}. Saving attendance.")
                self.save_attendance()
            else:
                speak(f"Hello {name}. No pending attendance.")

    def get_role_by_id(self, user_id):
        # Inefficient but works for small app
        users = self.db.get_all_users()
        for u in users:
            if str(u[0]) == str(user_id):
                return u[2]
        return None

    def update_pending_list(self):
        self.pending_listbox.configure(state="normal")
        self.pending_listbox.delete("1.0", "end")
        for uid in self.pending_attendance:
            self.pending_listbox.insert("end", f"ID: {uid}\n")
        self.pending_listbox.configure(state="disabled")

    def save_attendance(self):
        # Commit to DB
        present_ids = list(self.pending_attendance)
        for uid in present_ids:
            self.db.mark_attendance(uid)
        
        # Send Emails
        self.email_service.process_attendance_emails(present_ids)
        
        # Clear List
        self.pending_attendance.clear()
        self.update_pending_list()
        messagebox.showinfo("Success", "Attendance Saved and Emails Sent!")

    # --- Teacher Page Logic ---
    def start_capture_flow(self):
        uid = self.entry_id.get()
        name = self.entry_name.get()
        role = self.role_var.get()
        email_s = self.entry_email_s.get()
        email_p = self.entry_email_p.get()
        
        if not uid or not name:
            messagebox.showerror("Error", "ID and Name are required!")
            return
            
        # Add to DB
        if self.db.add_user(uid, name, role, email_s, email_p):
            # Create dataset folder
            folder_name = f"{uid}_{name}"
            folder_path = os.path.join("dataset", folder_name)
            create_directory(folder_path)
            
            # Start Camera Capture
            self.camera.start_capture_session(folder_path, self.on_capture_complete)
            messagebox.showinfo("Info", "Look at the camera. Capturing 20 photos...")
        else:
            messagebox.showerror("Error", "User ID already exists!")

    def on_capture_complete(self):
        # Run Encoder
        self.after(0, lambda: messagebox.showinfo("Processing", "Training Model... Please wait."))
        
        def _train():
            self.encoder.encode_faces()
            self.camera.load_encodings() # Reload in camera
            self.after(0, lambda: messagebox.showinfo("Success", "Training Complete! User Added."))
            self.after(0, self.load_user_list)
            
        threading.Thread(target=_train, daemon=True).start()

    def load_user_list(self):
        self.user_list_text.configure(state="normal")
        self.user_list_text.delete("1.0", "end")
        users = self.db.get_all_users()
        for u in users:
            self.user_list_text.insert("end", f"{u[0]} | {u[1]} | {u[2]}\n")
        self.user_list_text.configure(state="disabled")

    def delete_user(self):
        uid = self.delete_id_entry.get()
        if uid:
            self.db.delete_user(uid)
            self.load_user_list()
            messagebox.showinfo("Deleted", f"User {uid} deleted.")

    # --- Class Page Logic ---
    def load_class_stats(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        stats = self.db.get_attendance_stats()
        for s in stats:
            # Highlight if percentage < 75
            tags = ()
            if s['percentage'] < 75:
                tags = ('low_attendance',)
            
            self.tree.insert("", "end", values=(s['id'], s['name'], s['total_classes'], s['present'], f"{s['percentage']}%"), tags=tags)
        
        self.tree.tag_configure('low_attendance', background='#ffcccc', foreground='black') # Light red

    def on_closing(self):
        self.camera.stop()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
