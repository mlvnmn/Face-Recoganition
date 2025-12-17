import sqlite3
from datetime import datetime
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name="smartguard.db"):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                email_student TEXT,
                email_parent TEXT
            )
        ''')

        # Attendance Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                date TEXT,
                time TEXT,
                status TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_user(self, user_id, name, role, email_student, email_parent):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (id, name, role, email_student, email_parent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, role, email_student, email_parent))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def delete_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        cursor.execute('DELETE FROM attendance WHERE user_id = ?', (user_id,)) # Optional: keep history or delete
        conn.commit()
        conn.close()

    def get_all_users(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        conn.close()
        return users

    def get_students(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'Student'")
        students = cursor.fetchall()
        conn.close()
        return students

    def mark_attendance(self, user_id, status="Present"):
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        if self.check_attendance_today(user_id, date_str):
            return False # Already marked

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance (user_id, date, time, status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, date_str, time_str, status))
        conn.commit()
        conn.close()
        return True

    def check_attendance_today(self, user_id, date_str):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM attendance WHERE user_id = ? AND date = ?
        ''', (user_id, date_str))
        record = cursor.fetchone()
        conn.close()
        return record is not None

    def get_attendance_stats(self):
        # Returns a list of dictionaries with stats for each student
        conn = sqlite3.connect(self.db_name)
        
        # Get all students
        students = self.get_students()
        stats = []
        
        for student in students:
            s_id, s_name, _, _, _ = student
            
            # Total unique dates in attendance table (assuming classes happen on these days)
            # Or just count total attendance records for this user
            # For simplicity, let's assume total_classes is the count of distinct dates recorded in the system
            # A better approach might be to have a separate 'sessions' table, but we'll stick to the requested schema.
            # We will count how many days *any* attendance was taken as "Total Classes"
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
            total_classes = cursor.fetchone()[0]
            if total_classes == 0:
                total_classes = 1 # Avoid division by zero
            
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ? AND status = 'Present'", (s_id,))
            present_count = cursor.fetchone()[0]
            
            percentage = (present_count / total_classes) * 100
            
            stats.append({
                "id": s_id,
                "name": s_name,
                "total_classes": total_classes,
                "present": present_count,
                "percentage": round(percentage, 2)
            })
            
        conn.close()
        return stats
