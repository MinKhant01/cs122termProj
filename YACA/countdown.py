import tkinter as tk
import pygame
import sqlite3

class Countdown(tk.Frame):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.master = master
        self.user_id = user_id
        self.running_timers = {}

        pygame.mixer.init()

        self.add_button = tk.Button(self, text="Add Countdown", command=self.add_countdown)
        self.add_button.pack(pady=10)

        self.saved_label = tk.Label(self, text="Saved Countdowns", font=("Helvetica", 14))
        self.saved_label.pack()

        self.saved_frame = tk.Frame(self)
        self.saved_frame.pack(pady=10)

        self.saved_listbox = tk.Listbox(self.saved_frame, height=5, selectmode=tk.MULTIPLE)
        self.saved_listbox.pack(side="left", fill="y")
        self.saved_listbox.bind('<<ListboxSelect>>', self.on_select_saved)

        self.saved_scrollbar = tk.Scrollbar(self.saved_frame, orient="vertical")
        self.saved_scrollbar.config(command=self.saved_listbox.yview)
        self.saved_scrollbar.pack(side="right", fill="y")

        self.saved_listbox.config(yscrollcommand=self.saved_scrollbar.set)

        self.activate_button = tk.Button(self, text="Activate Timer", command=self.start, state=tk.DISABLED)
        self.activate_button.pack(pady=10)

        self.delete_button = tk.Button(self, text="Delete Countdown", command=self.delete_countdown, state=tk.DISABLED)
        self.delete_button.pack(pady=10)

        self.active_label = tk.Label(self, text="Active Countdowns", font=("Helvetica", 14))
        self.active_label.pack()

        self.active_frame = tk.Frame(self)
        self.active_frame.pack(pady=10)

        self.active_listbox = tk.Listbox(self.active_frame, height=2, selectmode=tk.MULTIPLE)
        self.active_listbox.pack(side="left", fill="y")
        self.active_listbox.bind('<<ListboxSelect>>', self.on_select_active)

        self.active_scrollbar = tk.Scrollbar(self.active_frame, orient="vertical")
        self.active_scrollbar.config(command=self.active_listbox.yview)
        self.active_scrollbar.pack(side="right", fill="y")

        self.active_listbox.config(yscrollcommand=self.active_scrollbar.set)

        self.terminate_button = tk.Button(self, text="Terminate Timer", command=self.terminate, state=tk.DISABLED)
        self.terminate_button.pack(pady=10)

        self.alarm_windows = {}

        self.db_connection = sqlite3.connect('path_to_your_database.db')
        self.create_table_if_not_exists()
        self.load_saved_countdowns()

        self.update_clock()

    def create_table_if_not_exists(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS countdowns (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id TEXT,
                            hours INTEGER,
                            minutes INTEGER,
                            seconds INTEGER,
                            label TEXT,
                            active INTEGER DEFAULT 1
                          )''')
        self.db_connection.commit()

    def on_select_saved(self, event):
        if self.saved_listbox.curselection():
            self.activate_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.activate_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def on_select_active(self, event):
        if self.active_listbox.curselection():
            self.terminate_button.config(state=tk.NORMAL)
        else:
            self.terminate_button.config(state=tk.DISABLED)

    def add_countdown(self):
        self.new_window = tk.Toplevel(self.master)
        self.new_window.title("Set Countdown")

        self.hours_var = tk.StringVar(self.new_window)
        self.minutes_var = tk.StringVar(self.new_window)
        self.seconds_var = tk.StringVar(self.new_window)
        self.label_var = tk.StringVar(self.new_window)

        tk.Label(self.new_window, text="Hours").pack(side="left", padx=5)
        self.hours_menu = tk.OptionMenu(self.new_window, self.hours_var, *[f"{i:02}" for i in range(24)])
        self.hours_menu.pack(side="left", padx=5)

        tk.Label(self.new_window, text="Minutes").pack(side="left", padx=5)
        self.minutes_menu = tk.OptionMenu(self.new_window, self.minutes_var, *[f"{i:02}" for i in range(60)])
        self.minutes_menu.pack(side="left", padx=5)

        tk.Label(self.new_window, text="Seconds").pack(side="left", padx=5)
        self.seconds_menu = tk.OptionMenu(self.new_window, self.seconds_var, *[f"{i:02}" for i in range(60)])
        self.seconds_menu.pack(side="left", padx=5)

        self.label_entry = tk.Entry(self.new_window, textvariable=self.label_var, font=("Helvetica", 14))
        self.label_entry.pack(pady=10)

        self.save_button = tk.Button(self.new_window, text="Save", command=self.save_countdown)
        self.save_button.pack(pady=10)

    def load_saved_countdowns(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT hours, minutes, seconds, label FROM countdowns WHERE active = 1 AND user_id = ?", (self.user_id,))
        for row in cursor.fetchall():
            hours, minutes, seconds, label = row
            self.saved_listbox.insert(tk.END, f"{hours:02}:{minutes:02}:{seconds:02} - {label}")

    def save_countdown(self):
        hours = int(self.hours_var.get() or 0)
        minutes = int(self.minutes_var.get() or 0)
        seconds = int(self.seconds_var.get() or 0)
        label = self.label_var.get()
        total_seconds = hours * 3600 + minutes * 60 + seconds
        if total_seconds > 0:
            self.saved_listbox.insert(tk.END, f"{hours:02}:{minutes:02}:{seconds:02} - {label}")
            cursor = self.db_connection.cursor()
            cursor.execute("INSERT INTO countdowns (user_id, hours, minutes, seconds, label) VALUES (?, ?, ?, ?, ?)",
                           (self.user_id, hours, minutes, seconds, label))
            self.db_connection.commit()
        self.new_window.destroy()

    def start(self):
        selected = self.saved_listbox.curselection()
        if selected:
            for index in selected:
                time_str = self.saved_listbox.get(index).split(' - ')[0]
                hours, minutes, seconds = map(int, time_str.split(':'))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                self.running_timers[time_str] = total_seconds
                self.active_listbox.insert(tk.END, time_str)
            self.activate_button.config(state=tk.DISABLED)

    def terminate(self):
        selected = self.active_listbox.curselection()
        if selected:
            for index in selected[::-1]:
                time_str = self.active_listbox.get(index)
                if time_str in self.running_timers:
                    del self.running_timers[time_str]
                self.active_listbox.delete(index)
                hours, minutes, seconds = map(int, time_str.split(':'))
                cursor = self.db_connection.cursor()
                cursor.execute("UPDATE countdowns SET active = 0 WHERE hours = ? AND minutes = ? AND seconds = ? AND user_id = ?",
                               (hours, minutes, seconds, self.user_id))
                self.db_connection.commit()
            self.terminate_button.config(state=tk.DISABLED)

    def delete_countdown(self):
        selected = self.saved_listbox.curselection()
        if selected:
            for index in selected[::-1]:
                time_str, label = self.saved_listbox.get(index).split(' - ')
                hours, minutes, seconds = map(int, time_str.split(':'))
                self.saved_listbox.delete(index)
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM countdowns WHERE hours = ? AND minutes = ? AND seconds = ? AND label = ? AND user_id = ?",
                               (hours, minutes, seconds, label, self.user_id))
                self.db_connection.commit()
            self.delete_button.config(state=tk.DISABLED)
            self.activate_button.config(state=tk.DISABLED)

    def reset(self):
        self.running_timers.clear()
        self.active_listbox.delete(0, tk.END)

    def update_clock(self):
        for time_str in list(self.running_timers.keys()):
            if self.running_timers[time_str] > 0:
                self.running_timers[time_str] -= 1
                hours, remainder = divmod(self.running_timers[time_str], 3600)
                minutes, seconds = divmod(remainder, 60)
                updated_time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                if time_str in self.active_listbox.get(0, tk.END):
                    index = self.active_listbox.get(0, tk.END).index(time_str)
                    self.active_listbox.delete(index)
                    self.active_listbox.insert(index, updated_time_str)
                    self.running_timers[updated_time_str] = self.running_timers.pop(time_str)
            else:
                del self.running_timers[time_str]
                if time_str in self.active_listbox.get(0, tk.END):
                    index = self.active_listbox.get(0, tk.END).index(time_str)
                    self.active_listbox.delete(index)
                self.show_turn_off_window(time_str)
        self.after(1000, self.update_clock)

    def show_turn_off_window(self, time_str):
        turn_off_window = tk.Toplevel(self.master)
        turn_off_window.title("Countdown Finished")

        label = tk.Label(turn_off_window, text=f"Time's up for {time_str}!", font=("Helvetica", 24))
        label.pack(pady=20)

        turn_off_button = tk.Button(turn_off_window, text="Turn Off", command=lambda: self.turn_off(time_str))
        turn_off_button.pack(pady=10)

        self.alarm_windows[time_str] = turn_off_window
        pygame.mixer.music.load("alarm.wav")
        pygame.mixer.music.play(-1)  # play the sound in a loop

    def turn_off(self, time_str):
        if time_str in self.alarm_windows:
            self.alarm_windows[time_str].destroy()
            del self.alarm_windows[time_str]
        pygame.mixer.music.stop()

    def __del__(self):
        if hasattr(self, 'db_connection'):
            self.db_connection.close()
