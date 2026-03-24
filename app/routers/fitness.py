from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta

from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase

router = APIRouter(
    prefix="/api/v1/fitness",
    tags=["Fitness"]
)


@router.get("/summary")
def get_fitness_summary(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    # last 24 hours
    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    resp = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .gte("recorded_at", since)
        .execute()
    )

    data = resp.data or []

    steps = 0
    heart_rates = []
    sleep_minutes = 0

    for row in data:
        t = row["type"]

        if t == "steps":
            steps += row["value"]

        elif t == "heart_rate":
            heart_rates.append(row["value"])

        elif t == "sleep_minutes":
            sleep_minutes += row["value"]

    avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else 0

    # simple calorie estimate
    calories = steps * 0.04

    # activity level logic
    if steps < 3000:
        activity = "low"
    elif steps < 8000:
        activity = "moderate"
    else:
        activity = "active"

    return {
        "status": "success",
        "data": {
            "steps": steps,
            "calories_burned": round(calories, 2),
            "avg_heart_rate": round(avg_hr, 2),
            "sleep_minutes": sleep_minutes,
            "activity_level": activity
        }
    }