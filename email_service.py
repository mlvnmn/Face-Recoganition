import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database_manager import DatabaseManager

# CONFIGURATION
# NOTE: To use Gmail, you must enable 2-Factor Authentication and generate an App Password.
# Go to Google Account -> Security -> 2-Step Verification -> App Passwords.
SENDER_EMAIL = "your_email@gmail.com" 
APP_PASSWORD = "your_app_password"

class EmailService:
    def __init__(self):
        self.db = DatabaseManager()

    def send_email(self, recipient, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"Email sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {e}")

    def process_attendance_emails(self, present_ids):
        """
        Runs the email sending process in a background thread.
        """
        threading.Thread(target=self._process_emails_thread, args=(present_ids,), daemon=True).start()

    def _process_emails_thread(self, present_ids):
        students = self.db.get_students()
        
        present_students = []
        absent_students = []

        for student in students:
            s_id, s_name, _, s_email, p_email = student
            if s_id in present_ids:
                present_students.append((s_name, s_email))
            else:
                absent_students.append((s_name, p_email))

        # Send Present Emails
        for name, email in present_students:
            if email:
                self.send_email(
                    email, 
                    "Attendance Confirmation", 
                    f"Hi {name},\n\nYou have been marked PRESENT for today's class.\n\nRegards,\nSmartGuard System"
                )

        # Send Absent Emails
        for name, email in absent_students:
            if email:
                self.send_email(
                    email, 
                    "Absent Alert", 
                    f"Dear Parent,\n\nYour ward {name} was marked ABSENT for today's class.\n\nPlease contact the administration if this is a mistake.\n\nRegards,\nSmartGuard System"
                )
