from flask import Flask, render_template
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent.parent / "config" / "secrets.env")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")  # default to localhost

app = Flask(__name__)

# Build the PostgreSQL connection string
POSTGRES_CONN_STRING = (
    f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST}"
)

sql = f"""
    Select 
        recorded_at
        , temperature_f
        , weather_temp_f
    From 
        logs
    Order By 
        Recorded_at desc
    Limit 100
    """
@app.route("/")
def dashboard():
    readings = []
    error = None
    # Connect to the PostgreSQL database
    
    try:
        with psycopg2.connect(POSTGRES_CONN_STRING) as conn:
            with conn.cursor() as cur:
                # Execute a query to fetch the latest 100 readings
                cur.execute(sql)
                readings = cur.fetchall()
    
    except psycopg2.Error as db_error:
        error = f"Database error: {db_error.pgerror or db_error}"
        print(f"Database error: {error}")
    except Exception as e:
        error = f"An error occurred: {str(e)}"
        print(f"An error occurred: {error}")

    return render_template("dashboard.html", readings=readings, error=error)

if __name__ == "__main__":
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)