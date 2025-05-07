import json
import os
import psycopg2
import requests
from datetime import datetime
from dotenv import load_dotenv

# --------------------------
# Load configuration
# --------------------------
load_dotenv("config/secrets.env")  # Load variables from config file

# Load sensitive config values
OWM_API_KEY = os.getenv("OWM_API_KEY")
LATITUDE = os.getenv("LAT")
LONGITUDE = os.getenv("LON")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")  # default to localhost
TARGET_SENSOR_ID = int(os.getenv("TARGET_SENSOR_ID"))

# Build the PostgreSQL connection string
POSTGRES_CONN_STRING = (
    f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST}"
)

# --------------------------
# Functions
# --------------------------

# Function to convert Celsius to Fahrenheit
def convert_celsius_to_fahrenheit(temp_celsius):
    """Convert Celsius to Fahrenheit."""
    return round((temp_celsius * 9 / 5) + 32, 2)

# Function to fetch weather data from OpenWeatherMap
def fetch_current_weather():
    """Fetch current weather conditions from OpenWeatherMap API."""
    weather_url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LATITUDE}&lon={LONGITUDE}&units=metric&appid={OWM_API_KEY}"
    )
    response = requests.get(weather_url)
    weather_data = response.json()

    return {
        "weather_temp_c": weather_data["main"]["temp"],
        "weather_temp_f": convert_celsius_to_fahrenheit(weather_data["main"]["temp"]),
        "feels_like_c": weather_data["main"]["feels_like"],
        "feels_like_f": convert_celsius_to_fahrenheit(weather_data["main"]["feels_like"]),
        "weather_main": weather_data["weather"][0]["main"],
        "weather_description": weather_data["weather"][0]["description"],
        "humidity": weather_data["main"]["humidity"],
        "cloudiness_pct": weather_data["clouds"]["all"],
        "wind_speed_mps": weather_data["wind"]["speed"],
        "wind_direction_deg": weather_data["wind"]["deg"],
        "pressure_hpa": weather_data["main"]["pressure"]
    }


# Function to insert a reading into the PostgreSQL database
def insert_into_database(timestamp, pool_temp_celsius):
    """Insert pool temperature and current weather into PostgreSQL."""
    pool_temp_fahrenheit = convert_celsius_to_fahrenheit(pool_temp_celsius)
    weather = fetch_current_weather()

    with psycopg2.connect(POSTGRES_CONN_STRING) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs (
                    recorded_at, temperature_c, temperature_f,
                    weather_temp_c, weather_temp_f,
                    feels_like_c, feels_like_f,
                    weather_main, weather_description,
                    humidity, cloudiness_pct, wind_speed_mps,
                    wind_direction_deg, pressure_hpa
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                timestamp, pool_temp_celsius, pool_temp_fahrenheit,
                weather["weather_temp_c"], weather["weather_temp_f"],
                weather["feels_like_c"], weather["feels_like_f"],
                weather["weather_main"], weather["weather_description"],
                weather["humidity"], weather["cloudiness_pct"],
                weather["wind_speed_mps"], weather["wind_direction_deg"],
                weather["pressure_hpa"]
            ))
        conn.commit()

# Function to read RTL_433 output and process Inkbird sensor data
def monitor_sensor():
    """Listen to rtl_433 and process matching sensor data."""
    print("[INFO] Monitoring started... Waiting for sensor data.")

    with os.popen("rtl_433 -F json") as rtl_output:
        for line in rtl_output:
            try:
                sensor_reading = json.loads(line.strip())

                # Check model and sensor ID match
                model = sensor_reading.get("model", "")
                sensor_id = sensor_reading.get("id")

                if model.startswith("Inkbird") and sensor_id == TARGET_SENSOR_ID:
                    timestamp = datetime.strptime(sensor_reading["time"], "%Y-%m-%d %H:%M:%S")
                    temperature_c = sensor_reading["temperature_C"]

                    insert_into_database(timestamp, temperature_c)
                    print(f"[✓] Logged reading from sensor {sensor_id} at {timestamp} — {temperature_c}°C")
                else:
                    print(f"[→] Skipped sensor {sensor_id} from model {model}")

            except Exception as error:
                print(f"[!] Error processing line: {error}")

# --------------------------
# Run Script
# --------------------------
if __name__ == "__main__":
    monitor_sensor()