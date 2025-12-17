# SmartGuard Ultimate - Face Recognition Attendance System

## Setup Instructions

1.  **Install Dependencies:**
    Ensure you have Python 3.9+ installed.
    Run the following command to install the required libraries:
    ```bash
    # Activate the virtual environment first (PowerShell)
    .\.venv\Scripts\Activate.ps1
    
    # 1. Download dlib wheel manually if it fails to install:
    # Download this file: https://github.com/zra/dlib-wheels/releases/download/v19.24.2/dlib-19.24.2-cp311-cp311-win_amd64.whl
    # Place it in this folder and run:
    pip install dlib-19.24.2-cp311-cp311-win_amd64.whl
    
    # 2. Then install other dependencies
    pip install -r requirements.txt
    ```
    *Note: If you encounter "Script is not signed" errors, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first.*

2.  **Email Configuration:**
    Open `email_service.py` and update the following lines with your Gmail credentials:
    ```python
    SENDER_EMAIL = "your_email@gmail.com"
    APP_PASSWORD = "your_app_password"
    ```
    *You must generate an App Password from your Google Account Security settings.*

3.  **Run the Application:**
    ```bash
    python main.py
    ```

## Usage Guide

1.  **Teacher Admin Page:**
    - Go to the "Teacher Admin" tab.
    - Add yourself as a **Teacher** first.
    - Click "Capture Photos & Train". The camera will take 20 photos.
    - Wait for the "Training Complete" message.
    - Add **Students** similarly.

2.  **Taking Attendance:**
    - Go to the "Home / Attendance" tab.
    - When a **Student** is detected, they are added to the "Pending List".
    - When a **Teacher** is detected, the system saves the attendance and sends emails.

3.  **Class Dashboard:**
    - View attendance statistics and identify students with low attendance (<75%).

## Troubleshooting
- If the camera doesn't open, check if another app is using it.
- If face recognition is slow, try reducing the resolution in `camera_service.py`.
