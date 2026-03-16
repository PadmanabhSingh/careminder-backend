from fastapi import APIRouter, HTTPException, Query
import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")

router = APIRouter(
    prefix="/api/v1/weather",
    tags=["Weather"]
)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


@router.get("/current")
def get_current_weather(
    lat: float = Query(...),
    lon: float = Query(...)
):
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="Missing OPENWEATHER_API_KEY")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    resp = requests.get(url, params=params, timeout=15)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()

    return {
        "status": "success",
        "data": {
            "location": data.get("name"),
            "temperature_c": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "weather": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"]
        }
    }