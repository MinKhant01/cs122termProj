# Yet Another Clock App (YACA)

YACA is a lightweight desktop application that integrates various functionalities such as a clock, weather updates, news headlines, calendar events, alarms, countdown timers, and a virtual assistant.

## Main Components

### YACA.py
This is the main file that initializes and manages the entire application. It sets up the user interface using Tkinter and integrates various modules to provide the following functionalities:
- **Clock**: Displays the current time and date.
- **Weather**: Fetches and displays current weather data and a 10-day forecast.
- **News**: Fetches and displays the latest news headlines.
- **Calendar**: Fetches and displays Google Calendar events.
- **Alarms**: Allows users to set and manage alarms.
- **Countdown**: Allows users to set and manage countdown timers.
- **Virtual Assistant**: Provides voice command functionalities using speech recognition and text-to-speech.

### Related Files

- **stopwatch.py**: Contains the `Stopwatch` class used for the stopwatch functionality.
- **clockface.py**: Contains the `ClockFace` class used to display the current time.
- **alarms.py**: Contains the `Alarms` class used to manage alarms.
- **countdown.py**: Contains the `Countdown` class used to manage countdown timers.
- **news.py**: Contains functions to fetch news headlines from various sources.
- **weather.py**: Contains functions to fetch and parse weather data.
- **signin.py**: Contains the `SignInPage` class used for Google sign-in functionality.
- **google_cal.py**: Contains functions to fetch Google Calendar events.

## How to Run

1. Ensure you have all the required dependencies installed.
2. Set up your environment variables in a `.env` file.
3. Run the `YACA.py` file to start the application.

## Environment Variables

- `NYTimesAPIKey`: API key for New York Times.
- `NewsAPIKey`: API key for NewsAPI.
- `OpenWeatherMapKey`: API key for OpenWeatherMap.
- `GoogleClientID`: Client ID for Google OAuth.
- `GoogleClientSecret`: Client Secret for Google OAuth.

## Features

- **Clock**: Displays the current time and date.
- **Weather**: Provides current weather information and a 10-day forecast.
- **News**: Displays the latest news headlines.
- **Calendar**: Shows upcoming Google Calendar events.
- **Alarms**: Allows setting and managing alarms.
- **Countdown**: Allows setting and managing countdown timers.
- **Virtual Assistant**: Responds to voice commands for various functionalities.

## Voice Commands

- "What time is it?"
- "What date is it?"
- "What day is it?"
- "How's the weather today?"
- "What's the temperature today?"
- "What's the humidity today?"
- "What's the precipitation today?"
- "What time is the sunrise today?"
- "What time is the sunset today?"
- "What's new today?"
- "Who am I?"
- "Thank you"
- "Tell me a lie"
- "Humor me"
- "Terminate"

## License

This project is licensed under the MIT License.