import tkinter as tk
import webbrowser
import threading
import time
from datetime import datetime, timedelta  # Add timedelta import
from stopwatch import Stopwatch
from clockface import ClockFace
from alarms import Alarms
from countdown import Countdown
from news import get_top_headlines  # Import the get_top_headlines function
from weather import get_weather_data, get_forecast_data, parse_weather_data, parse_forecast_data, get_current_coordinates, get_city_name  # Import weather functions
from signin import SignInPage
from google_sso import google_login, get_user_info
import mysql.connector  # Import mysql.connector
from dotenv import load_dotenv  # Import load_dotenv
import os  # Import os
from google_cal import get_google_calendar_events  # Import the function to get calendar events

# Load environment variables from .env file
load_dotenv()

class YACA:
    def __init__(self, root, user_info):
        self.root = root
        self.user_info = user_info
        self.root.title(f"YACA - Logged in as {self.user_info['first_name']} {self.user_info['last_name']}")
        
        # Set the size of the application window
        window_width = 1200  # Set your desired width
        window_height = 850  # Set your desired height
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(window_width, window_height)  # Set the minimum size
        
        self.center_window(window_width, window_height)  # Center the window
        
        self.unit_var = tk.StringVar()
        self.unit_var.set("Imperial")  # Default value
        
        self.create_menu()
        self.create_logout_button()  # Add this line to create the logout button
        
        self.root.grid_rowconfigure(0, weight=0)  # Ensure the top row does not expand
        self.root.grid_rowconfigure(1, weight=1)  # Adjust the weight of other rows
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_rowconfigure(4, weight=1)  # Add an extra row for the forecast button
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        
        self.logout_button = tk.Button(self.root, text="Logout", command=self.logout)
        self.logout_button.grid(row=0, column=0, sticky="nw", padx=(10, 0), pady=(10, 0))  # Position the logout button
        
        self.profile_label = tk.Label(root, text=f"Logged in as: {self.user_info['first_name']} {self.user_info['last_name']}", font=("Helvetica", 12), width=30, anchor="e")
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))  # Align to the right with padding
        
        self.clock_face = ClockFace(root)  # Initialize the ClockFace
        self.clock_face.grid(row=0, column=1, pady=(10, 0), sticky="n")  # Use grid layout and reduce padding
        
        self.date_label = tk.Label(root, font=("Helvetica", 16))
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.update_date()
        
        self.weather_frame = tk.Frame(root)  # Initialize the Weather frame
        self.weather_frame.grid(row=2, column=0, pady=10, sticky="nsew")  # Adjust grid position
        
        self.weather_title_frame = tk.Frame(self.weather_frame)  # Create a frame for the weather title
        self.weather_title_frame.pack(pady=(2, 5))  # Reduce top padding

        self.weather_title = tk.Label(self.weather_title_frame, text="Today's Weather", font=("Helvetica", 16, "bold"))
        self.weather_title.pack(side="left")

        self.current_weather_table = tk.Frame(self.weather_frame)
        self.current_weather_table.pack(pady=(10, 0))  # Adjust padding to push down the table

        self.forecast_button = tk.Button(self.weather_frame, text="View 10-Day Forecast", command=self.show_forecast)
        self.forecast_button.pack(pady=(5, 10))  # Adjust padding to push down the button
        
        self.calendar_frame = tk.Frame(root)  # Initialize the Calendar frame
        self.calendar_frame.grid(row=2, column=1, pady=10, sticky="nsew")  # Adjust grid position
        
        self.calendar_title_frame = tk.Frame(self.calendar_frame)  # Create a frame for the title and dropdown
        self.calendar_title_frame.pack(pady=(2, 5))  # Reduce top padding
        
        self.calendar_title = tk.Label(self.calendar_title_frame, text="Calendar Events For: ", font=("Helvetica", 16, "bold"))
        self.calendar_title.pack(side="left")
        
        self.calendar_option = tk.StringVar(self.calendar_frame)
        self.calendar_option.set(f"Today ({datetime.now().strftime('%Y-%m-%d')})")  # Default value
        
        self.calendar_dropdown = tk.OptionMenu(self.calendar_title_frame, self.calendar_option, *self.get_next_seven_days(), command=self.update_calendar_events)
        self.calendar_dropdown.pack(side="left")
        
        self.refresh_button = tk.Button(self.calendar_title_frame, text="Refresh", command=self.refresh_calendar_events)
        self.refresh_button.pack(side="left", padx=(10, 0))  # Add padding to the left
        
        self.calendar_display_frame = tk.Frame(self.calendar_frame)
        self.calendar_display_frame.pack(pady=10, fill="both", expand=True)
        
        self.calendar_scrollbar = tk.Scrollbar(self.calendar_display_frame, orient="vertical")
        self.calendar_scrollbar.pack(side="right", fill="y")
        
        self.calendar_listbox = tk.Text(self.calendar_display_frame, height=10, width=100, yscrollcommand=self.calendar_scrollbar.set, state=tk.DISABLED)
        self.calendar_listbox.pack(side="left", fill="both", expand=True)
        
        self.calendar_scrollbar.config(command=self.calendar_listbox.yview)
        
        self.fetch_calendar_events()  # Fetch and display calendar events initially
        self.root.after(60000, self.auto_refresh_calendar_events)  # Schedule automatic refresh every 60 seconds
        
        self.news_frame = tk.Frame(root)  # Initialize the News frame
        self.news_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")  # Make the news frame fill the remaining space
        self.news_frame.grid_rowconfigure(0, weight=0)
        self.news_frame.grid_rowconfigure(1, weight=1)
        self.news_frame.grid_columnconfigure(0, weight=1)
        
        self.news_title_frame = tk.Frame(self.news_frame)  # Create a frame for the news title and refresh button
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
        
        self.stopwatch_frame = None  # Initialize stopwatch_frame to None
        self.stopwatch = None  # Initialize stopwatch to None
        
        self.alarms_frame = None  # Initialize alarms_frame to None
        self.alarms = None  # Initialize alarms to None
        
        self.countdown_frame = None  # Initialize countdown_frame to None
        self.countdown = None  # Initialize countdown to None
        
        self.news_fetching = False  # Add a flag to indicate if news is being fetched
        self.news_cache = None  # Add a cache for news headlines
        self.news_cache_time = None  # Add a timestamp for the cache
        self.cache_duration = 600  # Cache duration in seconds (e.g., 10 minutes)
        
        self.forecast_frame = None  # Initialize forecast_frame to None
        
        self.update_clock()
        self.root.after(0, self.fetch_news)  # Fetch and display news initially
        self.root.after(0, self.fetch_weather)  # Fetch and display weather initially
        self.root.after(300000, self.auto_refresh_news)  # Schedule automatic news refresh every 5 minutes
        self.show_clock()  # Show the clock view initially
        self.ensure_user_in_db(user_info)  # Ensure the user is in the database

        self.calendar_option.trace_add('write', lambda *args: self.update_calendar_events(self.calendar_option.get()))

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
        self.logout_button.grid(row=0, column=0, sticky="nw", padx=(10, 0), pady=(10, 0))  # Position the logout button

    def logout(self):
        if self.root.winfo_exists():  # Check if the root window exists
            self.root.destroy()  # Destroy the current root window
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
            self.stopwatch_frame.grid_forget()  # Ensure the stopwatch frame is hidden
        if self.alarms_frame:
            self.alarms_frame.grid_forget()  # Ensure the alarms frame is hidden
        if self.countdown_frame:
            self.countdown_frame.grid_forget()  # Ensure the countdown frame is hidden
        self.news_frame.grid_forget()
        self.clock_face.grid(row=0, column=1, pady=(10, 0), sticky="n")  # Center the clock face
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.weather_frame.grid(row=2, column=0, pady=10, sticky="nsew")  # Show the weather frame in the left column
        self.calendar_frame.grid(row=2, column=1, pady=10, sticky="nsew")  # Show the calendar frame in the right column
        self.news_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")  # Show the news frame below the calendar frame
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))  # Ensure profile label is at the top right
        if not self.news_fetching:  # Check if news is already being fetched
            current_time = time.time()
            if self.news_cache and (current_time - self.news_cache_time < self.cache_duration):
                self.display_news(self.news_cache, 0)  # Use cached news if valid
            else:
                self.fetch_news()  # Fetch and display news when the clock view is shown
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
            self.alarms_frame.grid_forget()  # Ensure the alarms frame is hidden
        if self.countdown_frame:
            self.countdown_frame.grid_forget()  # Ensure the countdown frame is hidden
        self.stopwatch_frame.grid(row=5, column=0, pady=20, sticky="n")  # Use grid instead of pack
        self.calendar_frame.grid_forget()  # Ensure the calendar frame is hidden
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))  # Ensure profile label is at the top right
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def show_alarms(self):
        if self.alarms_frame is None:
            self.alarms_frame = tk.Frame(self.root)
            self.ensure_user_in_db(self.user_info)  # Ensure the user is in the database
            self.alarms = Alarms(self.alarms_frame, self.user_info['id'])  # Pass user_id to Alarms
            self.alarms_frame.grid(row=5, column=0, pady=20, sticky="n")  # Use grid instead of pack
            self.alarms.pack()  # Ensure the Alarms instance is packed within the frame

        self.clock_face.grid_forget()
        self.weather_frame.grid_forget()
        self.forecast_button.grid_forget()
        self.news_frame.grid_forget()
        if self.stopwatch_frame:
            self.stopwatch_frame.grid_forget()  # Ensure the stopwatch frame is hidden
        if self.countdown_frame:
            self.countdown_frame.grid_forget()  # Ensure the countdown frame is hidden
        self.alarms_frame.grid(row=5, column=0, pady=20, sticky="n")  # Use grid instead of pack
        self.calendar_frame.grid_forget()  # Ensure the calendar frame is hidden
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))  # Ensure profile label is at the top right
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def show_countdown(self):
        if self.countdown_frame is None:
            self.countdown_frame = tk.Frame(self.root)
            self.countdown = Countdown(self.countdown_frame)  # Create an instance of Countdown within the frame
            self.countdown.pack()  # Ensure the Countdown instance is packed within the frame

        self.clock_face.grid_forget()
        self.weather_frame.grid_forget()
        self.forecast_button.grid_forget()
        self.news_frame.grid_forget()
        if self.stopwatch_frame:
            self.stopwatch_frame.grid_forget()  # Ensure the stopwatch frame is hidden
        if self.alarms_frame:
            self.alarms_frame.grid_forget()  # Ensure the alarms frame is hidden
        self.countdown_frame.grid(row=5, column=0, pady=20, sticky="n")  # Use grid instead of pack
        self.calendar_frame.grid_forget()  # Ensure the calendar frame is hidden
        self.date_label.grid(row=1, column=1, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.profile_label.grid(row=0, column=2, sticky="ne", padx=(0, 10))  # Ensure profile label is at the top right
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def show_news(self):
        # Removed the show_news method
        pass

    def fetch_news(self):
        self.news_fetching = True  # Set the flag to True when fetching news
        self.news_listbox.config(state=tk.NORMAL)  # Enable editing to update content
        self.news_listbox.delete(1.0, tk.END)
        self.news_listbox.insert(tk.END, "Your News Feed is loading...\n")
        
        def fetch_news_thread():
            start_time = time.time()
            headlines = get_top_headlines()  # Use the function from news.py
            end_time = time.time()
            time_taken = end_time - start_time
            if self.root.winfo_exists():
                self.root.after(0, self.display_news, headlines, time_taken)
        
        self.root.after(0, fetch_news_thread)

    def display_news(self, headlines, time_taken):
        self.news_fetching = False  # Reset the flag when news fetching is done
        self.news_cache = headlines  # Cache the fetched news
        self.news_cache_time = time.time()  # Update the cache timestamp
        self.news_listbox.config(state=tk.NORMAL)  # Enable editing to update content
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
        self.news_listbox.config(state=tk.DISABLED)  # Disable editing after updating content

    def open_url(self, url):
        if url:
            webbrowser.open(url)

    def fetch_weather(self):
        def fetch_weather_thread():
            try:
                lat, lon = get_current_coordinates()  # Get the user's current coordinates
                city = get_city_name(lat, lon)  # Get the city name from the coordinates
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
            precipitation = self.current_weather['precipitation'] / 25.4  # Convert mm to inches
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
        self.forecast_frame = tk.Frame(forecast_window)  # Initialize forecast_frame here
        self.selected_date = tk.StringVar(forecast_window)
        self.selected_date.set("All")  # Default value
        
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
                precipitation = day['precipitation'] / 25.4  # Convert mm to inches
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
        self.clock_face.update_time()  # Ensure this method exists in ClockFace
        self.root.after(10, self.update_clock)  # Update every 10 milliseconds

    def start_stop(self):
        if self.stopwatch.running:
            self.stopwatch.stop()
            self.start_stop_button.config(text="Start")
            self.lap_reset_button.config(text="Reset")
        else:
            self.stopwatch.start()
            self.start_stop_button.config(text="Stop")
            self.lap_reset_button.config(text="Lap")

    def lap_reset(self):
        if self.stopwatch.running:
            self.lap()
        else:
            self.reset()

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
        print(f"Connecting to DB with host={os.getenv('MYSQL_HOST')}, user={os.getenv('MYSQL_USER')}, database={os.getenv('MYSQL_DATABASE')}")  # Debug print
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_info['id'],))
        user = cursor.fetchone()
        conn.close()
        print(f"Checking user in DB: {user_info['id']} - Found: {user}")  # Debug print
        return user is not None

    def ensure_user_in_db(self, user_info):
        if not self.check_user_in_db(user_info):
            conn = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DATABASE')
            )
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (id, name, email) VALUES (%s, %s, %s)
            ''', (user_info['id'], f"{user_info['first_name']} {user_info['last_name']}", user_info['email']))
            conn.commit()
            conn.close()

    def refresh_calendar_events(self):
        self.calendar_listbox.config(state=tk.NORMAL)  # Enable editing to update content
        self.calendar_listbox.delete(1.0, tk.END)
        self.calendar_listbox.insert(tk.END, "Refreshing Calendar Events ...\n")
        self.calendar_listbox.config(state=tk.DISABLED)  # Disable editing after updating content
        self.root.after(100, self.fetch_calendar_events)  # Fetch and display calendar events after a short delay

    def fetch_calendar_events(self):
        try:
            self.all_events = []  # Clear previous events
            self.calendar_listbox.config(state=tk.NORMAL)  # Enable editing to update content
            self.calendar_listbox.delete(1.0, tk.END)  # Clear the listbox
            events = get_google_calendar_events(self.user_info['email'])  # Pass the user's email
            self.all_events = events  # Store all events
            self.root.after(0, self.update_calendar_dropdown)  # Update the dropdown menu with the latest dates
            self.root.after(0, lambda: self.update_calendar_events(self.calendar_option.get()))  # Update display based on selected option
            print("Fetched and displayed calendar events.")
        except Exception as e:
            print(f"Error fetching calendar events: {e}")

    def update_calendar_dropdown(self):
        menu = self.calendar_dropdown["menu"]
        menu.delete(0, "end")
        for day in self.get_next_seven_days():
            menu.add_command(label=day, command=lambda value=day: self.calendar_option.set(value))
        self.update_calendar_events(self.calendar_option.get())  # Ensure the events are updated when the dropdown is updated

    def display_calendar_events(self, events):
        self.calendar_listbox.config(state=tk.NORMAL)  # Enable editing to update content
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
        self.calendar_listbox.config(state=tk.DISABLED)  # Disable editing after updating content

    def get_next_seven_days(self):
        days = [f"Today ({datetime.now().strftime('%Y-%m-%d')})"]
        for i in range(1, 7):
            date = (datetime.now() + timedelta(days=i))
            day = date.strftime("%A (%Y-%m-%d)")
            days.append(day)
        return days

    def update_calendar_events(self, option):
        self.calendar_listbox.config(state=tk.NORMAL)  # Enable editing to update content
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
        self.calendar_listbox.config(state=tk.DISABLED)  # Disable editing after updating content

    def auto_refresh_calendar_events(self):
        threading.Thread(target=self.fetch_calendar_events).start()  # Fetch and display calendar events in a separate thread
        self.root.after(60000, self.auto_refresh_calendar_events)  # Schedule the next refresh

    def auto_refresh_news(self):
        self.fetch_news()  # Fetch and display news
        self.root.after(300000, self.auto_refresh_news)  # Schedule the next refresh

if __name__ == "__main__":
    def on_success(current_root, user_info):
        if current_root.winfo_exists():  # Check if the current root window exists
            current_root.destroy()  # Destroy the current root window
        new_root = tk.Tk()  # Create a new root window
        app = YACA(new_root, user_info)
        new_root.mainloop()
    
    root = tk.Tk()
    SignInPage(root, lambda user_info: on_success(root, user_info))
    root.mainloop()