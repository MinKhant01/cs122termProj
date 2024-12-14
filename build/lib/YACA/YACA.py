import tkinter as tk
import webbrowser
import threading
import time
from datetime import datetime, timedelta
from stopwatch import Stopwatch
from clockface import ClockFace
from alarms import Alarms
from countdown import Countdown
from news import get_top_headlines
from weather import get_weather_data, get_forecast_data, parse_weather_data, parse_forecast_data, get_current_coordinates, get_city_name
from signin import SignInPage
from google_sso import google_login, get_user_info
import speech_recognition as sr                     # Import speech_recognition for VA's speech recognition
import pyttsx3                                      # Import pyttsx3 for VA's text-to-speech
import sqlite3                                      # lightweight portable db to save alarms & coutdowns with user_id
import os
from google_cal import get_google_calendar_events
from dotenv import load_dotenv
load_dotenv()

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def schedule_tooltip(self, event=None):
        self.cancel_tooltip()
        self.tooltip_id = self.widget.after(2000, self.show_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="black", relief="solid", borderwidth=1, font=("Helvetica", 10))
        label.pack()

    def hide_tooltip(self, event=None):
        self.cancel_tooltip()
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def cancel_tooltip(self):
        if hasattr(self, 'tooltip_id'):
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None

class YACA:
    def __init__(self, root, user_info):
        self.root = root
        self.user_info = user_info
        self.root.title(f"YACA - Logged in as {self.user_info['first_name']} {self.user_info['last_name']}")
        
        # Set the size of the application window
        window_width = 1200                                         # Set the desired width
        window_height = 850                                         # Set the desired height
        self.root.geometry(f"{window_width}x{window_height}")       # Set the window size
        self.root.minsize(window_width, window_height)              # Set the minimum size
        
        self.center_window(window_width, window_height)             # Center the window
        
        self.unit_var = tk.StringVar()                              # scale for temperature and precipitation
        self.unit_var.set("Imperial")                               # default scale
        
        self.create_menu()
        self.create_logout_button()
        
        self.va_process = None                                      # initialize the virtual assistant
        
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        
        # logout button
        self.logout_button = tk.Button(self.root, text="Logout", command=self.logout)
        self.logout_button.grid(row=0, column=0, sticky="nw", padx=(10, 0), pady=(10, 0))
        
        # listen button
        self.listen_button = tk.Button(self.root, text="Assistant", command=self.listen_for_command)
        self.listen_button.grid(row=0, column=1, sticky="nw", padx=(10, 0), pady=(10, 0))
        
        # profile label
        self.profile_label = tk.Label(root, text=f"Logged in as: {self.user_info['first_name']} {self.user_info['last_name']}", font=("Helvetica", 12), width=30, anchor="e")
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))
        
        # main clock face
        self.clock_face = ClockFace(root)
        self.clock_face.grid(row=0, column=1, pady=(10, 0), sticky="n")
        
        # date label
        self.date_label = tk.Label(root, font=("Helvetica", 16))
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")
        self.update_date()
        
        # weather frame
        self.weather_frame = tk.Frame(root)
        self.weather_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        
        self.weather_title_frame = tk.Frame(self.weather_frame)
        self.weather_title_frame.pack(pady=(2, 5))

        self.weather_title = tk.Label(self.weather_title_frame, text="Today's Weather", font=("Helvetica", 16, "bold"))
        self.weather_title.pack(side="left")

        self.current_weather_table = tk.Frame(self.weather_frame)
        self.current_weather_table.pack(pady=(10, 0))

        # add forecast button to complement the weather frame
        self.forecast_button = tk.Button(self.weather_frame, text="View 10-Day Forecast", command=self.show_forecast)
        self.forecast_button.pack(pady=(5, 10))
        
        # calendar frame
        self.calendar_frame = tk.Frame(root)
        self.calendar_frame.grid(row=2, column=1, pady=10, sticky="nsew")
        
        self.calendar_title_frame = tk.Frame(self.calendar_frame)
        self.calendar_title_frame.pack(pady=(2, 5))
        
        self.calendar_title = tk.Label(self.calendar_title_frame, text="Calendar Events For: ", font=("Helvetica", 16, "bold"))
        self.calendar_title.pack(side="left")
        
        # default calendar dropdown option
        self.calendar_option = tk.StringVar(self.calendar_frame)
        self.calendar_option.set(f"Today ({datetime.now().strftime('%Y-%m-%d')})")
        
        self.calendar_dropdown = tk.OptionMenu(self.calendar_title_frame, self.calendar_option, *self.get_next_seven_days(), command=self.update_calendar_events)
        self.calendar_dropdown.pack(side="left")
        
        self.refresh_button = tk.Button(self.calendar_title_frame, text="Refresh", command=self.refresh_calendar_events)
        self.refresh_button.pack(side="left", padx=(10, 0))
        
        self.calendar_display_frame = tk.Frame(self.calendar_frame)
        self.calendar_display_frame.pack(pady=10, fill="both", expand=True)
        
        self.calendar_scrollbar = tk.Scrollbar(self.calendar_display_frame, orient="vertical")
        self.calendar_scrollbar.pack(side="right", fill="y")
        
        self.calendar_listbox = tk.Text(self.calendar_display_frame, height=10, width=100, yscrollcommand=self.calendar_scrollbar.set, state=tk.DISABLED)
        self.calendar_listbox.pack(side="left", fill="both", expand=True)
        
        self.calendar_scrollbar.config(command=self.calendar_listbox.yview)
        
        self.fetch_calendar_events()                                                # initial fetch and display of calendar events
        self.root.after(60000, self.auto_refresh_calendar_events)                   # scheduled automatic refresh every 60 seconds
        
        # news frame
        self.news_frame = tk.Frame(root)
        self.news_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")
        self.news_frame.grid_rowconfigure(0, weight=0)
        self.news_frame.grid_rowconfigure(1, weight=1)
        self.news_frame.grid_columnconfigure(0, weight=1)
        
        self.news_title_frame = tk.Frame(self.news_frame)
        self.news_title_frame.grid(row=0, column=0, pady=(10, 0), sticky="ew")
        
        self.news_title = tk.Label(self.news_title_frame, text="Today's Top News", font=("Helvetica", 16, "bold"))
        self.news_title.pack(side="left", padx=(10, 0))
        
        self.news_refresh_button = tk.Button(self.news_title_frame, text="Refresh", command=self.fetch_news)
        self.news_refresh_button.pack(side="left", padx=(10, 0))
        
        self.news_listbox = tk.Text(self.news_frame, height=20, width=100, state=tk.DISABLED)
        self.news_listbox.grid(row=1, column=0, sticky="nsew")
        
        self.news_scrollbar = tk.Scrollbar(self.news_frame, orient="vertical")
        self.news_scrollbar.config(command=self.news_listbox.yview)
        self.news_scrollbar.grid(row=1, column=1, sticky="ns")
        
        self.news_listbox.config(yscrollcommand=self.news_scrollbar.set)
        
        # stopwatch init
        self.stopwatch_frame = None
        self.stopwatch = None
        
        # alarms init
        self.alarms_frame = None
        self.alarms = None
        
        # countdown init
        self.countdown_frame = None
        self.countdown = None
        
        self.news_fetching = False
        self.news_cache = None
        self.news_cache_time = None
        self.cache_duration = 600                                           # system cache duration in seconds, total of 10 mins
        
        self.forecast_frame = None  # Initialize forecast_frame to None
        
        self.update_clock()
        self.root.after(0, self.fetch_news)
        self.root.after(0, self.fetch_weather)
        self.root.after(300000, self.auto_refresh_news)
        self.show_clock()
        self.create_users_table()
        self.ensure_user_in_db(user_info)                                     # ensure the user is in the database

        self.calendar_option.trace_add('write', lambda *args: self.update_calendar_events(self.calendar_option.get()))
        self.create_virtual_assistant()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Clock", command=self.show_clock)
        view_menu.add_command(label="Stopwatch", command=self.show_stopwatch)
        view_menu.add_command(label="Alarms", command=self.show_alarms)
        view_menu.add_command(label="Countdown", command=self.show_countdown)
        
        units_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Units", menu=units_menu)
        units_menu.add_radiobutton(label="Metric", variable=self.unit_var, value="Metric", command=self.update_units)
        units_menu.add_radiobutton(label="Imperial", variable=self.unit_var, value="Imperial", command=self.update_units)

    def create_logout_button(self):
        self.logout_button = tk.Button(self.root, text="Logout", command=self.logout)
        self.logout_button.grid(row=0, column=0, sticky="nw", padx=(10, 0), pady=(10, 0))

    def logout(self):
        if self.root.winfo_exists():            # check if the root window exists
            self.root.destroy()                 # destroy the current root window
        new_root = tk.Tk()
        SignInPage(new_root, lambda user_info: on_success(new_root, user_info))
        new_root.mainloop()

    def update_units(self):
        self.update_weather_display()
        self.update_forecast_display()

    def update_date(self):
        today = datetime.now().strftime("%a, %B %d")
        self.date_label.config(text=today)

    def show_clock(self):
        if self.stopwatch_frame:
            self.stopwatch_frame.grid_forget()                      # ensure the stopwatch frame is hidden
        if self.alarms_frame:
            self.alarms_frame.grid_forget()                         # ensure the alarms frame is hidden
        if self.countdown_frame:
            self.countdown_frame.grid_forget()                      # ensure the countdown frame is hidden
        self.news_frame.grid_forget()
        self.clock_face.grid(row=0, column=1, pady=(10, 0), sticky="n")
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")
        self.weather_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        self.calendar_frame.grid(row=2, column=1, pady=10, sticky="nsew")
        self.news_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))
        if not self.news_fetching:
            current_time = time.time()
            if self.news_cache and (current_time - self.news_cache_time < self.cache_duration):
                self.display_news(self.news_cache, 0)
            else:
                self.fetch_news() 
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def show_stopwatch(self):
        if self.stopwatch_frame is None:
            self.stopwatch_frame = tk.Frame(self.root)
            self.stopwatch = Stopwatch()
            
            self.label = tk.Label(self.stopwatch_frame, text="00:00.00", font=("Helvetica", 48))
            self.label.pack()
            
            self.start_stop_button = tk.Button(self.stopwatch_frame, text="Start", command=self.start_stop)
            self.start_stop_button.pack(side="left", padx=10)
            
            self.lap_reset_button = tk.Button(self.stopwatch_frame, text="Lap", command=self.lap_reset)
            self.lap_reset_button.pack(side="left", padx=10)
            
            self.lap_frame = tk.Frame(self.stopwatch_frame)
            self.lap_frame.pack(side="left", padx=10)
            
            self.lap_listbox = tk.Listbox(self.lap_frame, height=5)
            self.lap_listbox.pack(side="left", fill="y")
            
            self.scrollbar = tk.Scrollbar(self.lap_frame, orient="vertical")
            self.scrollbar.config(command=self.lap_listbox.yview)
            self.scrollbar.pack(side="right", fill="y")
            
            self.lap_listbox.config(yscrollcommand=self.scrollbar.set)

        self.clock_face.grid_forget()
        self.weather_frame.grid_forget()
        self.forecast_button.grid_forget()
        self.news_frame.grid_forget()
        if self.alarms_frame:
            self.alarms_frame.grid_forget()
        if self.countdown_frame:
            self.countdown_frame.grid_forget()
        self.stopwatch_frame.grid(row=5, column=0, pady=20, sticky="n")
        self.calendar_frame.grid_forget()
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def show_alarms(self):
        if self.alarms_frame is None:
            self.alarms_frame = tk.Frame(self.root)
            self.ensure_user_in_db(self.user_info)
            self.alarms = Alarms(self.alarms_frame, self.user_info['id'], self.save_alarm_callback)
            self.alarms_frame.grid(row=5, column=0, pady=20, sticky="n")
            self.alarms.pack()

        self.clock_face.grid_forget()
        self.weather_frame.grid_forget()
        self.forecast_button.grid_forget()
        self.news_frame.grid_forget()
        if self.stopwatch_frame:
            self.stopwatch_frame.grid_forget()
        if self.countdown_frame:
            self.countdown_frame.grid_forget()
        self.alarms_frame.grid(row=5, column=0, pady=20, sticky="n")
        self.calendar_frame.grid_forget()
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def show_countdown(self):
        if self.countdown_frame is None:
            self.countdown_frame = tk.Frame(self.root)
            self.countdown = Countdown(self.countdown_frame, self.user_info['id'])
            self.countdown.pack()

        self.clock_face.grid_forget()
        self.weather_frame.grid_forget()
        self.forecast_button.grid_forget()
        self.news_frame.grid_forget()
        if self.stopwatch_frame:
            self.stopwatch_frame.grid_forget()
        if self.alarms_frame:
            self.alarms_frame.grid_forget()
        self.countdown_frame.grid(row=5, column=0, pady=20, sticky="n")
        self.calendar_frame.grid_forget()
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def fetch_news(self):
        self.news_fetching = True
        self.news_listbox.config(state=tk.NORMAL)
        self.news_listbox.delete(1.0, tk.END)
        self.news_listbox.insert(tk.END, "Your News Feed is loading...\n")
        
        def fetch_news_thread():
            start_time = time.time()
            headlines = get_top_headlines()
            end_time = time.time()
            time_taken = end_time - start_time
            if self.root.winfo_exists():
                self.root.after(0, self.display_news, headlines, time_taken)
        
        self.root.after(0, fetch_news_thread)

    def display_news(self, headlines, time_taken):
        self.news_fetching = False                      # reset the flag when news fetching is done
        self.news_cache = headlines                     # cache the fetched news
        self.news_cache_time = time.time()              # update the cache timestamp
        self.news_listbox.config(state=tk.NORMAL)       # enable editing to update content
        self.news_listbox.delete(1.0, tk.END)
        for headline in headlines:
            self.news_listbox.insert(tk.END, f"Title: {headline['title']}\n")
            self.news_listbox.insert(tk.END, f"Abstract: {headline['abstract']}\n")
            self.news_listbox.insert(tk.END, f"Source: {headline['source']}\n")
            self.news_listbox.insert(tk.END, f"Report Date: {headline['report_date']}\n")
            self.news_listbox.insert(tk.END, f"URL: {headline['url']}\n", ('url',))
            self.news_listbox.insert(tk.END, '-' * 40 + '\n')
            self.news_listbox.tag_config('url', foreground='light blue', underline=True)
            self.news_listbox.tag_bind('url', '<Enter>', lambda e: e.widget.config(cursor="hand2"))
            self.news_listbox.tag_bind('url', '<Leave>', lambda e: e.widget.config(cursor=""))
            self.news_listbox.tag_bind('url', '<Button-1>', lambda e, url=headline['url']: self.open_url(url))
        self.news_listbox.insert(tk.END, f"\nTotal Time: {time_taken:.2f} seconds\n")
        self.news_listbox.config(state=tk.DISABLED)     # disable editing after updating content

    def open_url(self, url):
        if url:
            webbrowser.open(url)

    def fetch_weather(self):
        def fetch_weather_thread():
            try:
                lat, lon = get_current_coordinates()                # get the user's current coordinates
                city = get_city_name(lat, lon)                      # get the city name from the coordinates
                weather_data = get_weather_data(lat, lon)
                forecast_data = get_forecast_data(lat, lon)
                current_weather = parse_weather_data(weather_data)
                forecast = parse_forecast_data(forecast_data)
                if self.root.winfo_exists():
                    self.root.after(0, self.display_weather, current_weather, forecast)
            except Exception as e:
                print(f"Error fetching weather data: {e}")
        
        self.root.after(0, fetch_weather_thread)

    def display_weather(self, current_weather, forecast):
        self.current_weather = current_weather
        self.forecast = forecast
        self.update_weather_display()

    def update_weather_display(self, _=None):
        for widget in self.current_weather_table.winfo_children():
            widget.destroy()
        
        headers = ["Temperature", "Humidity", "Precipitation", "Sunrise", "Sunset"]
        for row, header in enumerate(headers):
            label = tk.Label(self.current_weather_table, text=header, font=("Helvetica", 12, "bold"), borderwidth=1, relief="solid")
            label.grid(row=row, column=0, sticky="nsew")
        
        unit = self.unit_var.get()
        
        if unit == "Imperial":
            temperature = self.current_weather['temperature'] * 9/5 + 32
            temperature_str = f"{temperature:.1f} °F"
            precipitation = self.current_weather['precipitation'] / 25.4
            precipitation_str = f"{precipitation:.2f} in"
        else:
            temperature_str = f"{self.current_weather['temperature']} °C"
            precipitation_str = f"{self.current_weather['precipitation']} mm"
        
        values = [
            temperature_str,
            f"{self.current_weather['humidity']}%",
            precipitation_str,
            self.current_weather['sunrise'],
            self.current_weather['sunset']
        ]
        
        for row, value in enumerate(values):
            tk.Label(self.current_weather_table, text=value, borderwidth=1, relief="solid").grid(row=row, column=1, sticky="nsew")
        
        for col in range(2):
            self.current_weather_table.grid_columnconfigure(col, weight=1)

    def show_forecast(self):
        forecast_window = tk.Toplevel(self.root)
        forecast_window.title("10-Day Forecast")
        self.forecast_frame = tk.Frame(forecast_window)
        self.selected_date = tk.StringVar(forecast_window)
        self.selected_date.set("All")
        
        dates = ["All"] + [day['date'] for day in self.forecast]
        
        dropdown_frame = tk.Frame(forecast_window)
        dropdown_frame.pack(pady=10)
        
        label = tk.Label(dropdown_frame, text="Display Option : ", font=("Helvetica", 12))
        label.pack(side="left")
        
        dropdown = tk.OptionMenu(dropdown_frame, self.selected_date, *dates, command=self.update_forecast_display)
        dropdown.pack(side="left")
        
        self.forecast_frame = tk.Frame(forecast_window)
        self.forecast_frame.pack(pady=20)
        
        self.update_forecast_display("All")

    def update_forecast_display(self, _=None):
        if self.forecast_frame is None:
            return
        
        for widget in self.forecast_frame.winfo_children():
            widget.destroy()
        
        headers = ["Date", "Day", "Temperature Range", "Humidity", "Precipitation"]
        for col, header in enumerate(headers):
            label = tk.Label(self.forecast_frame, text=header, font=("Helvetica", 12, "bold"), borderwidth=1, relief="solid")
            label.grid(row=0, column=col, sticky="nsew")
        
        selected_date = self.selected_date.get()
        unit = self.unit_var.get()
        
        if selected_date == "All":
            forecast_data = self.forecast
        else:
            forecast_data = [day for day in self.forecast if day['date'] == selected_date]
        
        for row, day in enumerate(forecast_data, start=1):
            temp_min, temp_max = map(float, day['temperature_range'].split(' - '))
            if unit == "Imperial":
                temp_min = temp_min * 9/5 + 32
                temp_max = temp_max * 9/5 + 32
                precipitation = day['precipitation'] / 25.4
                temp_range = f"{temp_min:.1f} - {temp_max:.1f} °F"
                precipitation_str = f"{precipitation:.2f} in"
            else:
                temp_range = f"{temp_min:.1f} - {temp_max:.1f} °C"
                precipitation_str = f"{day['precipitation']} mm"
            
            tk.Label(self.forecast_frame, text=day['date'], borderwidth=1, relief="solid").grid(row=row, column=0, sticky="nsew")
            tk.Label(self.forecast_frame, text=day['day'], borderwidth=1, relief="solid").grid(row=row, column=1, sticky="nsew")
            tk.Label(self.forecast_frame, text=temp_range, borderwidth=1, relief="solid").grid(row=row, column=2, sticky="nsew")
            tk.Label(self.forecast_frame, text=f"{day['humidity']}%", borderwidth=1, relief="solid").grid(row=row, column=3, sticky="nsew")
            tk.Label(self.forecast_frame, text=precipitation_str, borderwidth=1, relief="solid").grid(row=row, column=4, sticky="nsew")
        
        for col in range(len(headers)):
            self.forecast_frame.grid_columnconfigure(col, weight=1)

    def update_clock(self):
        if self.stopwatch and self.stopwatch.running:
            self.stopwatch.update_time()
            self.label.config(text=self.stopwatch.get_time())
        self.clock_face.update_time()
        self.root.after(1000, self.update_clock)                        # Update every second

    def start_stop(self):
        if self.stopwatch.running:
            self.stopwatch.stop()
            self.start_stop_button.config(text="Start")
            self.lap_reset_button.config(text="Reset")
        else:
            self.stopwatch.start()
            self.start_stop_button.config(text="Stop")
            self.lap_reset_button.config(text="Lap")
            self.stopwatch_start_time = time.time()
            threading.Thread(target=self.run_stopwatch).start()

    def run_stopwatch(self):
        while self.stopwatch.running:
            elapsed_time = time.time() - self.stopwatch_start_time
            self.stopwatch.time = int(elapsed_time * 1000)
            self.label.config(text=self.stopwatch.get_time())
            time.sleep(0.1)

    def lap_reset(self):
        if self.stopwatch.running:
            self.lap()
        else:
            self.stopwatch.reset()
            self.label.config(text="00:00.00")
            self.lap_listbox.delete(0, tk.END)

    def reset(self):
        self.stopwatch.reset()
        self.label.config(text="00:00.00")
        self.start_stop_button.config(text="Start")
        self.lap_reset_button.config(text="Lap")
        self.lap_listbox.delete(0, tk.END)

    def lap(self):
        self.stopwatch.lap()
        self.lap_listbox.delete(0, tk.END)
        for i, lap_time in enumerate(self.stopwatch.laps):
            self.lap_listbox.insert(tk.END, f"Lap {i + 1}: {lap_time}")
        self.lap_listbox.yview_moveto(1)

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def check_user_in_db(self, user_info):
        conn = sqlite3.connect('/Users/ekhant/Documents/FA24/CS122/termProj/YACA/yaca.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_info['id'],))
        user = cursor.fetchone()
        conn.close()
        return user is not None

    def create_users_table(self):
        conn = sqlite3.connect('/Users/ekhant/Documents/FA24/CS122/termProj/YACA/yaca.db')
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

    def ensure_user_in_db(self, user_info):
        self.create_users_table()
        if not self.check_user_in_db(user_info):
            conn = sqlite3.connect('/Users/ekhant/Documents/FA24/CS122/termProj/YACA/yaca.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (id, name, email) VALUES (?, ?, ?)
            ''', (user_info['id'], f"{user_info['first_name']} {user_info['last_name']}", user_info['email']))
            conn.commit()
            conn.close()

    def refresh_calendar_events(self):
        self.calendar_listbox.config(state=tk.NORMAL)
        self.calendar_listbox.delete(1.0, tk.END)
        self.calendar_listbox.insert(tk.END, "Refreshing Calendar Events ...\n")
        self.calendar_listbox.config(state=tk.DISABLED)
        self.root.after(100, self.fetch_calendar_events)

    def fetch_calendar_events(self):
        try:
            self.all_events = []
            self.calendar_listbox.config(state=tk.NORMAL)
            self.calendar_listbox.delete(1.0, tk.END)
            events = get_google_calendar_events(self.user_info['email'])
            self.all_events = events
            self.root.after(0, self.update_calendar_dropdown)
            self.root.after(0, lambda: self.update_calendar_events(self.calendar_option.get()))
            print("Fetched and displayed calendar events.")
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            if 'invalid_grant' in str(e):
                token_file = f'token_{self.user_info["email"]}.json'
                if os.path.exists(token_file):
                    os.remove(token_file)
                    print("Removed invalid token file. Please log in again.")
                self.calendar_listbox.config(state=tk.NORMAL)
                self.calendar_listbox.delete(1.0, tk.END)
                self.calendar_listbox.insert(tk.END, "Invalid credentials. Please log in again.\n")
                self.calendar_listbox.config(state=tk.DISABLED)

    def update_calendar_dropdown(self):
        menu = self.calendar_dropdown["menu"]
        menu.delete(0, "end")
        for day in self.get_next_seven_days():
            menu.add_command(label=day, command=lambda value=day: self.calendar_option.set(value))
        self.update_calendar_events(self.calendar_option.get())

    def display_calendar_events(self, events):
        self.calendar_listbox.config(state=tk.NORMAL)
        self.calendar_listbox.delete(1.0, tk.END)
        
        if not events:
            self.calendar_listbox.insert(tk.END, "No upcoming events found.\n")
        else:
            for event in events:
                start = event.get_formatted_start_time()
                end = event.get_formatted_end_time()
                summary = event.get_summary()
                description = event.get_description()
                location = event.get_location()
                participants = ', '.join([attendee.get('email') for attendee in event.event.get('attendees', [])])
                
                self.calendar_listbox.insert(tk.END, f"Event Name: {summary}\n")
                if description:
                    self.calendar_listbox.insert(tk.END, f"Description: {description}\n")
                if location:
                    self.calendar_listbox.insert(tk.END, f"Location: {location}\n")
                self.calendar_listbox.insert(tk.END, f"Start Time: {start}\n")
                self.calendar_listbox.insert(tk.END, f"End Time: {end}\n")
                if participants:
                    self.calendar_listbox.insert(tk.END, f"Participants: {participants}\n")
                self.calendar_listbox.insert(tk.END, '-' * 40 + '\n')
        self.calendar_listbox.config(state=tk.DISABLED)

    def get_next_seven_days(self):
        days = [f"Today ({datetime.now().strftime('%Y-%m-%d')})"]
        for i in range(1, 7):
            date = (datetime.now() + timedelta(days=i))
            day = date.strftime("%A (%Y-%m-%d)")
            days.append(day)
        return days

    def update_calendar_events(self, option):
        self.calendar_listbox.config(state=tk.NORMAL)
        self.calendar_listbox.delete(1.0, tk.END)
        
        if option.startswith("Today"):
            selected_date = datetime.now().date()
        else:
            day_index = self.get_next_seven_days().index(option)
            selected_date = (datetime.now() + timedelta(days=day_index)).date()
        
        filtered_events = []
        for event in self.all_events:
            event_start = event.get_start_time()
            if event_start:
                event_date = datetime.fromisoformat(event_start).date()
                if event_date == selected_date:
                    filtered_events.append(event)
        
        if not filtered_events:
            self.calendar_listbox.insert(tk.END, "No upcoming events found.\n")
        else:
            self.display_calendar_events(filtered_events)
        self.calendar_listbox.config(state=tk.DISABLED)

    def auto_refresh_calendar_events(self):
        threading.Thread(target=self.fetch_calendar_events).start()
        self.root.after(60000, self.auto_refresh_calendar_events)

    def auto_refresh_news(self):
        self.fetch_news()
        self.root.after(300000, self.auto_refresh_news)

    def create_virtual_assistant(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()

    def listen_for_command(self):
        self.listen_button.config(text="Listening")
        self.root.update_idletasks()
        
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = self.recognizer.listen(source, timeout=5)
                command = self.recognizer.recognize_google(audio)
                print(f"You: {command}")
                response = self.process_va_command(command)
                print(f"Assistant: {response}")
                self.speak(response)
            except sr.WaitTimeoutError:
                print("Assistant: No command heard within the time limit.")
            except sr.UnknownValueError:
                print("Assistant: Sorry, I didn't catch that.")
                self.speak("Sorry, I didn't catch that.")
            except sr.RequestError as e:
                print(f"Assistant: Could not request results; {e}")
                self.speak(f"Could not request results; {e}")
            finally:
                self.listen_button.config(text="Assistant")
                self.root.update_idletasks()

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def process_va_command(self, command):
        command = command.lower()
        if "what time is it" in command:
            return datetime.now().strftime("%H:%M:%S")
        elif "what date is it" in command:
            return datetime.now().strftime("%A, %B %d, %Y")
        elif "what day is it" in command:
            return datetime.now().strftime("%A")
        elif "how's the weather today" in command:
            if hasattr(self, 'current_weather'):
                unit = self.unit_var.get()
                temperature = self.current_weather['temperature']
                humidity = self.current_weather['humidity']
                if unit == "Imperial":
                    temperature = temperature * 9/5 + 32
                    return f"Today's temperature is {temperature:.1f}°F and humidity is {humidity}%."
                else:
                    return f"Today's temperature is {temperature}°C and humidity is {humidity}%."
            else:
                return "Weather data is not available right now."
        elif "what's the temperature today" in command:
            if hasattr(self, 'current_weather'):
                unit = self.unit_var.get()
                temperature = self.current_weather['temperature']
                if unit == "Imperial":
                    temperature = temperature * 9/5 + 32
                    return f"Today's temperature is {temperature:.1f}°F."
                else:
                    return f"Today's temperature is {temperature}°C."
            else:
                return "Temperature data is not available right now."
        elif "what's the humidity today" in command:
            if hasattr(self, 'current_weather'):
                humidity = self.current_weather['humidity']
                return f"Today's humidity is {humidity}%."
            else:
                return "Humidity data is not available right now."
        elif "what's the precipitation today" in command:
            if hasattr(self, 'current_weather'):
                unit = self.unit_var.get()
                precipitation = self.current_weather['precipitation']
                if unit == "Imperial":
                    precipitation = precipitation / 25.4
                    return f"Today's precipitation is {precipitation:.2f} inches."
                else:
                    return f"Today's precipitation is {precipitation} mm."
            else:
                return "Precipitation data is not available right now."
        elif "what time is the sunrise today" in command:
            if hasattr(self, 'current_weather'):
                sunrise = self.current_weather['sunrise']
                sunrise_time = datetime.strptime(sunrise, "%I:%M:%S %p").strftime("%I %M %p").lstrip("0").replace(" 0", " ")
                return f"Today's sunrise is at {sunrise_time}."
            else:
                return "Sunrise data is not available right now."
        elif "what time is the sunset today" in command:
            if hasattr(self, 'current_weather'):
                sunset = self.current_weather['sunset']
                sunset_time = datetime.strptime(sunset, "%I:%M:%S %p").strftime("%I %M %p").lstrip("0").replace(" 0", " ")
                return f"Today's sunset is at {sunset_time}."
            else:
                return "Sunset data is not available right now."
        elif "what's new today" in command:
            if self.news_cache:
                top_news = self.news_cache[:3]
                news_titles = [news['title'] for news in top_news]
                return "Here are the top 3 news headlines: " + "; ".join(news_titles)
            else:
                return "News data is not available right now."
        elif "thank you" in command:
            return "You are very welcome!"
        elif "tell me a lie" in command:
            return "You are quite a handsome chap!"
        elif "humor me" in command:
            return "Why did the scarecrow win an award? Because he was outstanding in his field!"
        elif "terminate" in command:
            return "Talk to you later, ciao!"
        elif "who am i" in command:
            return f"You are {self.user_info['first_name']} {self.user_info['last_name']}."
        else:
            return "Sorry, I didn't understand that command."

    def save_alarm_callback(self):
        print("Alarm saved successfully.")

if __name__ == "__main__":
    def on_success(current_root, user_info):
        if current_root.winfo_exists():         # Check if the current root window exists
            current_root.destroy()              # Destroy the current root window
        new_root = tk.Tk()                      # Create a new root window
        app = YACA(new_root, user_info)
        new_root.mainloop()
    
    root = tk.Tk()
    SignInPage(root, lambda user_info: on_success(root, user_info))
    root.mainloop()