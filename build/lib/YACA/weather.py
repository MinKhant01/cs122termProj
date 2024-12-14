import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder

load_dotenv()

API_KEY = os.getenv('OpenWeatherMapKey')
BASE_URL = "http://api.openweathermap.org/data/2.5/"
GEOCODE_URL = "http://api.openweathermap.org/geo/1.0/direct"
REVERSE_GEOCODE_URL = "http://api.openweathermap.org/geo/1.0/reverse"
IP_GEOLOCATION_URL = "http://ip-api.com/json"

def get_current_coordinates():
    response = requests.get(IP_GEOLOCATION_URL)
    data = response.json()
    if data:
        lat, lon = data["lat"], data["lon"]
        print(f"Current Coordinates: Latitude = {lat}, Longitude = {lon}")
        return lat, lon
    else:
        raise ValueError("Unable to get current location")

def get_city_name(lat, lon):
    url = f"{REVERSE_GEOCODE_URL}?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data:
        city = data[0]["name"]
        print(f"City Name: {city}")
        return city
    else:
        raise ValueError("City not found")

def get_weather_data(lat, lon):
    url = f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    return response.json()

def get_forecast_data(lat, lon):
    url = f"{BASE_URL}forecast/daily?lat={lat}&lon={lon}&cnt=10&appid={API_KEY}&units=metric"
    response = requests.get(url)
    return response.json()

def parse_weather_data(data):
    lat, lon = data["coord"]["lat"], data["coord"]["lon"]
    tf = TimezoneFinder()
    local_tz = pytz.timezone(tf.timezone_at(lat=lat, lng=lon))
    weather_info = {
        "temperature": data["main"]["temp"],
        "air_quality": data.get("air_quality", "N/A"),
        "precipitation": data.get("rain", {}).get("1h", 0),
        "uv_index": data.get("uv_index", "N/A"),
        "humidity": data["main"]["humidity"],
        "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"], pytz.utc).astimezone(local_tz).strftime('%I:%M:%S %p'),
        "sunset": datetime.fromtimestamp(data["sys"]["sunset"], pytz.utc).astimezone(local_tz).strftime('%I:%M:%S %p')
    }
    return weather_info

def parse_forecast_data(data):
    local_tz = pytz.timezone(os.getenv('TZ', 'UTC'))
    forecast_info = []
    for day in data["list"]:
        day_info = {
            "date": datetime.fromtimestamp(day["dt"], pytz.utc).astimezone(local_tz).strftime('%Y-%m-%d'),
            "day": datetime.fromtimestamp(day["dt"], pytz.utc).astimezone(local_tz).strftime('%A'),
            "temperature_range": f"{day['temp']['min']} - {day['temp']['max']}",
            "humidity": day["humidity"],
            "precipitation": day.get("rain", 0)
        }
        forecast_info.append(day_info)
    return forecast_info

if __name__ == "__main__":
    lat, lon = get_current_coordinates()
    city = get_city_name(lat, lon)
    print(f"Fetching weather data for {city} (Coordinates: Latitude = {lat}, Longitude = {lon})")
    weather_data = get_weather_data(lat, lon)
    forecast_data = get_forecast_data(lat, lon)
    
    current_weather = parse_weather_data(weather_data)
    forecast = parse_forecast_data(forecast_data)
    
    print("Current Weather:", current_weather)
    print("10-Day Forecast:", forecast)
