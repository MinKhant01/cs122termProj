import tkinter as tk
import time

class ClockFace(tk.Label):
    def __init__(self, parent):
        super().__init__(parent, font=("Helvetica", 48))
        self.update_time()

    def update_time(self):
        current_time = time.strftime("%I:%M:%S %p")
        self.config(text=current_time)
        self.after(1000, self.update_time)
