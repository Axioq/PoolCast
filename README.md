# PoolCast

PoolCast tracks pool temperature readings from an Inkbird sensor, enriches each
reading with current weather data from OpenWeatherMap, stores the results in
PostgreSQL, and displays recent readings in a Flask dashboard.

## What It Does

- Listens for pool temperature sensor readings with `rtl_433`.
- Filters readings to a configured Inkbird sensor ID.
- Fetches current weather conditions from OpenWeatherMap.
- Stores pool and weather readings in a PostgreSQL `logs` table.
- Serves a Flask dashboard with temperature trends and current conditions.
- Supports dashboard ranges for 24 hours, 7 days, 30 days, and 1 year.

## Project Structure

```text
PoolCast/
|-- main.py                  # Sensor listener and database logger
|-- web/
|   |-- app.py               # Flask dashboard app
|   `-- templates/
|       `-- dashboard.html   # Dashboard UI
|-- config/
|   `-- secrets.env          # Local configuration, not committed
`-- README.md
```

## Requirements

- Python 3
- PostgreSQL
- `rtl_433`
- An OpenWeatherMap API key
- Python packages:
  - `flask`
  - `psycopg2-binary`
  - `python-dotenv`
  - `requests`

Install the Python dependencies with:

```bash
python3 -m pip install flask psycopg2-binary python-dotenv requests
```

## Configuration

Create a local secrets file at:

```text
config/secrets.env
```

Example:

```env
OWM_API_KEY=your_openweathermap_api_key
LAT=00.0000
LON=-00.0000
DB_NAME=poolcast
DB_USER=poolcast_user
DB_PASS=your_database_password
DB_HOST=localhost
TARGET_SENSOR_ID=12345
```

`config/secrets.env` is ignored by git and should not be committed.

## Database

PoolCast expects a PostgreSQL database with a `logs` table. The application uses
these columns:

```sql
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL,
    temperature_c NUMERIC,
    temperature_f NUMERIC,
    weather_temp_c NUMERIC,
    weather_temp_f NUMERIC,
    feels_like_c NUMERIC,
    feels_like_f NUMERIC,
    weather_main TEXT,
    weather_description TEXT,
    humidity INTEGER,
    cloudiness_pct INTEGER,
    wind_speed_mps NUMERIC,
    wind_direction_deg INTEGER,
    pressure_hpa INTEGER
);
```

## Running The Logger

Start the sensor listener from the project root:

```bash
python3 main.py
```

The logger runs `rtl_433 -F json`, watches for matching Inkbird readings, fetches
weather data, and inserts each reading into PostgreSQL.

## Running The Dashboard

Start the Flask dashboard from the project root:

```bash
python3 web/app.py
```

Open the dashboard at:

```text
http://localhost:5001
```

The Flask app listens on `0.0.0.0:5001`, so it can also be opened from another
device on the same network using the host machine's IP address:

```text
http://<host-ip>:5001
```

## Dashboard Routes

The dashboard is served at `/` and accepts a `range` query parameter:

```text
http://localhost:5001/?range=24h
http://localhost:5001/?range=7d
http://localhost:5001/?range=30d
http://localhost:5001/?range=1y
```

## Troubleshooting

- If the dashboard shows a database error, confirm PostgreSQL is running and the
  `DB_*` values in `config/secrets.env` are correct.
- If no data appears, confirm the `logs` table has rows for the selected time
  range.
- If the logger does not record readings, confirm `rtl_433` is installed and the
  `TARGET_SENSOR_ID` matches the Inkbird sensor ID.
- If weather calls fail, confirm `OWM_API_KEY`, `LAT`, and `LON` are set.
