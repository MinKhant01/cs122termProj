import tkinter as tk
import webbrowser
import threading
import time
from datetime import datetime
from stopwatch import Stopwatch
from clockface import ClockFace
from alarms import Alarms
from countdown import Countdown
from news import get_top_headlines  # Import the get_top_headlines function
from weather import get_weather_data, get_forecast_data, parse_weather_data, parse_forecast_data, get_current_coordinates, get_city_name  # Import weather functions
from signin import SignInPage
from google_sso import google_login, get_user_info

class YACA:
    def __init__(self, root, user_info):
        self.root = root
        self.user_info = user_info
        self.root.title(f"YACA - Logged in as {self.user_info['first_name']} {self.user_info['last_name']}")
        
        # Set the size of the application window
        window_width = 1200  # Set your desired width
        window_height = 600  # Set your desired height
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(window_width, window_height)  # Set the minimum size
        
        self.center_window(window_width, window_height)  # Center the window
        
        self.unit_var = tk.StringVar()
        self.unit_var.set("Imperial")  # Default value
        
        self.create_menu()
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_rowconfigure(4, weight=1)  # Add an extra row for the forecast button
        self.root.grid_columnconfigure(0, weight=1)
        
        self.clock_face = ClockFace(root)  # Initialize the ClockFace
        self.clock_face.grid(row=0, column=0, pady=(10, 0), sticky="n")  # Use grid layout and reduce padding
        
        self.date_label = tk.Label(root, font=("Helvetica", 16))
        self.date_label.grid(row=1, column=0, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.update_date()
        
        self.profile_label = tk.Label(root, text=f"Logged in as: {self.user_info['first_name']} {self.user_info['last_name']}", font=("Helvetica", 12), width=30, anchor="e")
        self.profile_label.grid(row=0, column=0, sticky="e", padx=(0, 10))  # Align to the right with padding
        
        self.weather_frame = tk.Frame(root)  # Initialize the Weather frame
        self.weather_frame.grid(row=2, column=0, pady=10, sticky="n")  # Reduce padding
        
        self.current_weather_table = tk.Frame(self.weather_frame)
        self.current_weather_table.pack(pady=10)  # Reduce padding
        
        self.forecast_button = tk.Button(root, text="View 10-Day Forecast", command=self.show_forecast)
        self.forecast_button.grid(row=3, column=0, pady=5, sticky="n")  # Reduce padding
        
        self.news_frame = tk.Frame(root)  # Initialize the News frame
        self.news_frame.grid(row=4, column=0, sticky="nsew")  # Make the news frame fill the remaining space
        self.news_frame.grid_rowconfigure(0, weight=1)
        self.news_frame.grid_columnconfigure(0, weight=1)
        
        self.news_listbox = tk.Text(self.news_frame, height=20, width=100)
        self.news_listbox.grid(row=0, column=0, sticky="nsew")
        
        self.news_scrollbar = tk.Scrollbar(self.news_frame, orient="vertical")
        self.news_scrollbar.config(command=self.news_listbox.yview)
        self.news_scrollbar.grid(row=0, column=1, sticky="ns")
        
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
        self.show_clock()  # Show the clock view initially

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
        self.clock_face.grid(row=0, column=0, pady=(10, 0), sticky="n")
        self.date_label.grid(row=1, column=0, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.weather_frame.grid(row=2, column=0, pady=10, sticky="n")  # Show the weather frame below the clock face
        self.forecast_button.grid(row=3, column=0, pady=5, sticky="n")  # Ensure the button is fully displayed
        self.news_frame.grid(row=4, column=0, sticky="nsew")  # Show the news frame below the weather frame
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
            self.start_stop_button.pack(side="left")
            
            self.lap_reset_button = tk.Button(self.stopwatch_frame, text="Lap", command=self.lap_reset)
            self.lap_reset_button.pack(side="left")
            
            self.lap_frame = tk.Frame(self.stopwatch_frame)
            self.lap_frame.pack(side="left")
            
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
        self.date_label.grid(row=1, column=0, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def show_alarms(self):
        if self.alarms_frame is None:
            self.alarms_frame = tk.Frame(self.root)
            self.alarms = Alarms(self.alarms_frame)  # Create an instance of Alarms within the frame
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
        self.date_label.grid(row=1, column=0, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
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
        self.date_label.grid(row=1, column=0, pady=(0, 10), sticky="n")  # Ensure date_label is always visible
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def show_news(self):
        # Removed the show_news method
        pass

    def fetch_news(self):
        self.news_fetching = True  # Set the flag to True when fetching news
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
        self.clock_face.update_time()  # Update the clock face time
        self.root.after(10, self.update_clock)

    def start_stop(self):
        if self.stopwatch.running:
            self.stopwatch.stop()
            self.start_stop_button.config(text="Stop")
            self.lap_reset_button.config(text="Lap")
        else:
            self.stopwatch.start()
            self.start_stop_button.config(text="Start")
            self.lap_reset_button.config(text="Reset")

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

if __name__ == "__main__":
    def on_success(user_info):
        root.destroy()
        new_root = tk.Tk()  # Create a new root window
        app = YACA(new_root, user_info)
        new_root.mainloop()
    
    root = tk.Tk()
    SignInPage(root, on_success)
    root.mainloop()
