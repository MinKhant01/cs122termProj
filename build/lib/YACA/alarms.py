import tkinter as tk
import sqlite3
from datetime import datetime, timedelta
import pygame
from dotenv import load_dotenv

class Alarms(tk.Frame):
    def __init__(self, parent, user_id, save_alarm_callback):
        super().__init__(parent)
        self.user_id = user_id
        self.save_alarm_callback = save_alarm_callback
        load_dotenv('/Users/ekhant/Documents/FA24/CS122/termProj/.env')
        self.db_connection = sqlite3.connect('/Users/ekhant/Documents/FA24/CS122/termProj/yaca.db')  # Connect to SQLite database
        self.db_cursor = self.db_connection.cursor()
        self.create_users_table()  # Ensure the users table is created
        self.create_table()
        self.create_widgets()
        self.load_alarms()
        self.check_alarms()
        self.alarm_triggered = False
        self.alarm_acknowledged = False
        self.alarm_window_open = False
        pygame.mixer.init()
        self.last_triggered_time = None

    def create_users_table(self):
        conn = sqlite3.connect('/Users/ekhant/Documents/FA24/CS122/termProj/YACA/yaca.db')  # Connect to SQLite database
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def create_table(self):
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                hour TEXT NOT NULL,
                minute TEXT NOT NULL,
                am_pm TEXT NOT NULL,
                label TEXT,
                repeat_option TEXT NOT NULL DEFAULT 'None',
                active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        self.db_connection.commit()

    def create_widgets(self):
        self.add_alarm_button = tk.Button(self, text="Add Alarm", command=self.open_add_alarm_window)
        self.add_alarm_button.pack(pady=10)
        
        self.alarms_frame = tk.Frame(self)
        self.alarms_frame.pack()

    def load_alarms(self):
        for widget in self.alarms_frame.winfo_children():
            widget.destroy()
        
        self.db_cursor.execute("SELECT * FROM alarms WHERE user_id = ?", (self.user_id,))
        alarms = self.db_cursor.fetchall()
        for alarm in alarms:
            alarm_frame = tk.Frame(self.alarms_frame)
            alarm_frame.pack(pady=5, fill="x")
            
            alarm_label = f"{alarm[2]}:{alarm[3]} {alarm[4]} - {alarm[5]} - {alarm[6]}"
            tk.Label(alarm_frame, text=alarm_label).pack(side="left", padx=5)
            
            tk.Button(alarm_frame, text="Edit", command=lambda a=alarm: self.open_edit_alarm_window(a)).pack(side="left", padx=5)
            tk.Button(alarm_frame, text="Delete", command=lambda a=alarm: self.delete_alarm(a[0])).pack(side="left", padx=5)
            toggle_text = "Deactivate" if alarm[7] else "Activate"
            tk.Button(alarm_frame, text=toggle_text, command=lambda a=alarm: self.toggle_alarm(a)).pack(side="left", padx=5)

    def toggle_alarm(self, alarm):
        new_status = 0 if alarm[7] else 1
        self.db_cursor.execute("UPDATE alarms SET active = ? WHERE id = ? AND user_id = ?", (new_status, alarm[0], self.user_id))
        self.db_connection.commit()
        self.load_alarms()

    def open_add_alarm_window(self):
        self.open_alarm_window()

    def open_edit_alarm_window(self, alarm):
        self.open_alarm_window(alarm)

    def open_alarm_window(self, alarm=None):
        alarm_window = tk.Toplevel(self)
        alarm_window.title("Edit Alarm" if alarm else "Add Alarm")

        now = datetime.now()
        current_hour = now.strftime("%I")
        current_minute = now.strftime("%M")
        current_am_pm = now.strftime("%p")

        hour_var = tk.StringVar(value=alarm[2] if alarm else current_hour)
        hour_options = [f"{i:02}" for i in range(1, 13)]
        tk.OptionMenu(alarm_window, hour_var, *hour_options).pack(side="left", padx=5)

        minute_var = tk.StringVar(value=alarm[3] if alarm else current_minute)
        minute_options = [f"{i:02}" for i in range(0, 60)]
        tk.OptionMenu(alarm_window, minute_var, *minute_options).pack(side="left", padx=5)
        
        am_pm_var = tk.StringVar(value=alarm[4] if alarm else current_am_pm)
        tk.OptionMenu(alarm_window, am_pm_var, "AM", "PM").pack(side="left", padx=5)
        
        tk.Label(alarm_window, text="Alarm Label").pack(side="left", padx=5)
        label_entry = tk.Entry(alarm_window, width=10)
        label_entry.insert(0, alarm[5] if alarm else "")
        label_entry.pack(side="left", padx=5)
        
        tk.Label(alarm_window, text="Repeat").pack(side="left", padx=5)
        repeat_var = tk.StringVar(value=alarm[6] if alarm else "None")
        repeat_options = ["None", "Every Sunday", "Every Monday", "Every Tuesday", "Every Wednesday", "Every Thursday", "Every Friday", "Every Saturday"]
        tk.OptionMenu(alarm_window, repeat_var, *repeat_options).pack(side="left", padx=5)
        
        def save_alarm():
            hour = hour_var.get()
            minute = minute_var.get()
            am_pm = am_pm_var.get()
            label = label_entry.get()
            repeat_option = repeat_var.get()

            if alarm:
                self.db_cursor.execute('''
                    UPDATE alarms
                    SET hour = ?, minute = ?, am_pm = ?, label = ?, repeat_option = ?, active = 1
                    WHERE id = ? AND user_id = ?
                ''', (hour, minute, am_pm, label, repeat_option, alarm[0], self.user_id))
            else:
                self.db_cursor.execute('''
                    INSERT INTO alarms (user_id, hour, minute, am_pm, label, repeat_option, active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (self.user_id, hour, minute, am_pm, label, repeat_option))
            self.db_connection.commit()
            alarm_window.destroy()
            self.load_alarms()

        def cancel_alarm():
            alarm_window.destroy()

        tk.Button(alarm_window, text="Save", command=save_alarm).pack(side="left", padx=5)
        tk.Button(alarm_window, text="Cancel", command=cancel_alarm).pack(side="left", padx=5)

    def delete_alarm(self, alarm_id):
        self.db_cursor.execute("DELETE FROM alarms WHERE id = ? AND user_id = ?", (alarm_id, self.user_id))
        self.db_connection.commit()
        self.load_alarms()

    def check_alarms(self):
        now = datetime.now()
        current_time = now.strftime("%I:%M %p")
        current_day = now.strftime("%A")
        self.db_cursor.execute("SELECT * FROM alarms WHERE active = 1 AND user_id = ?", (self.user_id,))
        alarms = self.db_cursor.fetchall()
        for alarm in alarms:
            alarm_time = f"{alarm[2]}:{alarm[3]} {alarm[4]}"
            if current_time == alarm_time and not self.alarm_triggered and not self.alarm_acknowledged:
                if self.last_triggered_time and (now - self.last_triggered_time) < timedelta(minutes=1):
                    continue
                if alarm[6] == "None" or alarm[6] == f"Every {current_day}":
                    self.alarm_triggered = True
                    self.alarm_acknowledged = True
                    self.last_triggered_time = now
                    self.trigger_alarm(alarm[5], alarm[2], alarm[3], alarm[4], alarm[6])
                    if alarm[6] == "None":
                        self.toggle_alarm(alarm)
        self.after(1000, self.check_alarms)

    def trigger_alarm(self, label, hour, minute, am_pm, repeat_option):
        if self.alarm_window_open:
            return

        def stop_alarm():
            alarm_window.destroy()
            pygame.mixer.music.stop()
            self.alarm_triggered = False
            self.alarm_acknowledged = False
            self.alarm_window_open = False

        self.alarm_window_open = True
        alarm_window = tk.Toplevel(self)
        alarm_window.title("Alarm")

        alarm_label = label if label else "Alarm"
        alarm_details = f"Time: {hour}:{minute} {am_pm}\nRepeat: {repeat_option}"

        tk.Label(alarm_window, text=f"Alarm: {alarm_label}", font=("Helvetica", 16, "bold")).pack(pady=10)
        tk.Label(alarm_window, text=alarm_details, font=("Helvetica", 12)).pack(pady=10)
        tk.Button(alarm_window, text="Turn Off", command=stop_alarm).pack(pady=10)

        print("Playing alarm sound...")
        pygame.mixer.music.load("alarm.wav")
        pygame.mixer.music.play(-1)
