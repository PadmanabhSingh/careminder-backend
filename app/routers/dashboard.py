from fastapi import APIRouter, Depends
from datetime import datetime, timedelta, timezone, date
from collections import defaultdict

from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)


@router.get("")
def get_dashboard(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    today = datetime.now(timezone.utc).date()
    start_7d = today - timedelta(days=6)
    start_7d_dt = datetime.combine(start_7d, datetime.min.time(), tzinfo=timezone.utc)
    end_tomorrow_dt = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    # Biomarkers for last 7 days
    biomarker_resp = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .gte("recorded_at", start_7d_dt.isoformat())
        .lt("recorded_at", end_tomorrow_dt.isoformat())
        .order("recorded_at", desc=False)
        .execute()
    )
    rows = biomarker_resp.data or []

    # Latest summary for today
    latest = {
        "heartRate": None,
        "systolicBP": None,
        "diastolicBP": None,
        "glucose": None,
        "oxygen": None,
        "sleepHours": None,
        "stressLevel": None,
        "date": today.isoformat()
    }

    today_rows_desc = sorted(
        [r for r in rows if (r.get("recorded_at") or "")[:10] == today.isoformat()],
        key=lambda r: r.get("recorded_at", ""),
        reverse=True
    )

    for row in today_rows_desc:
        biomarker_type = row.get("type")
        value = row.get("value")

        if biomarker_type == "heart_rate" and latest["heartRate"] is None:
            latest["heartRate"] = float(value)
        elif biomarker_type == "blood_pressure_systolic" and latest["systolicBP"] is None:
            latest["systolicBP"] = float(value)
        elif biomarker_type == "blood_pressure_diastolic" and latest["diastolicBP"] is None:
            latest["diastolicBP"] = float(value)
        elif biomarker_type == "blood_glucose" and latest["glucose"] is None:
            latest["glucose"] = float(value)
        elif biomarker_type == "spo2" and latest["oxygen"] is None:
            latest["oxygen"] = float(value)
        elif biomarker_type == "sleep_minutes" and latest["sleepHours"] is None:
            latest["sleepHours"] = float(value) / 60.0
        elif biomarker_type == "stress_level" and latest["stressLevel"] is None:
            latest["stressLevel"] = float(value)

    # Weekly chart preview
    date_list = [(start_7d + timedelta(days=i)).isoformat() for i in range(7)]
    day_index = {d: i for i, d in enumerate(date_list)}

    history = {
        "dates": date_list,
        "weeklyHeartRate": [None] * 7,
        "weeklySystolic": [None] * 7,
        "weeklyDiastolic": [None] * 7,
        "weeklyGlucose": [None] * 7,
        "weeklyOxygen": [None] * 7,
        "weeklySleep": [None] * 7,
        "weeklyStress": [None] * 7,
    }

    grouped = defaultdict(list)
    for row in rows:
        recorded_at = row.get("recorded_at")
        biomarker_type = row.get("type")
        value = row.get("value")
        if not recorded_at or biomarker_type is None or value is None:
            continue
        day_key = recorded_at[:10]
        if day_key not in day_index:
            continue
        grouped[(day_key, biomarker_type)].append(float(value))

    for (day_key, biomarker_type), values in grouped.items():
        idx = day_index[day_key]
        avg_value = sum(values) / len(values)

        if biomarker_type == "heart_rate":
            history["weeklyHeartRate"][idx] = avg_value
        elif biomarker_type == "blood_pressure_systolic":
            history["weeklySystolic"][idx] = avg_value
        elif biomarker_type == "blood_pressure_diastolic":
            history["weeklyDiastolic"][idx] = avg_value
        elif biomarker_type == "blood_glucose":
            history["weeklyGlucose"][idx] = avg_value
        elif biomarker_type == "spo2":
            history["weeklyOxygen"][idx] = avg_value
        elif biomarker_type == "sleep_minutes":
            history["weeklySleep"][idx] = avg_value / 60.0
        elif biomarker_type == "stress_level":
            history["weeklyStress"][idx] = avg_value

    # Fitness summary, last 24 hours
    since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    fitness_rows = [r for r in rows if (r.get("recorded_at") or "") >= since_24h]

    steps = 0
    heart_rates = []
    sleep_minutes = 0

    for row in fitness_rows:
        t = row.get("type")
        v = row.get("value", 0)

        if t == "steps":
            steps += v
        elif t == "heart_rate":
            heart_rates.append(v)
        elif t == "sleep_minutes":
            sleep_minutes += v

    avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else 0
    calories = steps * 0.04

    if steps < 3000:
        activity = "low"
    elif steps < 8000:
        activity = "moderate"
    else:
        activity = "active"

    fitness = {
        "steps": steps,
        "calories_burned": round(calories, 2),
        "avg_heart_rate": round(avg_hr, 2),
        "sleep_minutes": sleep_minutes,
        "activity_level": activity
    }

    # Recent alerts
    alerts_resp = (
        sb.table("alerts")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    alerts_rows = alerts_resp.data or []
    alerts = [
        {
            "id": row["id"],
            "message": row["message"],
            "severity": row["severity"],
            "created_at": row["created_at"]
        }
        for row in alerts_rows
    ]

    # Achievements summary
    ach_resp = (
        sb.table("achievements")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    ach_rows = ach_resp.data or []

    current_month = today.strftime("%Y-%m")
    monthly = sum(
        1 for row in ach_rows
        if (row.get("achieved_at") or "").startswith(current_month)
    )

    achievements = {
        "total": len(ach_rows),
        "monthly": monthly,
        "streak": min(len(ach_rows), 8)
    }

    return {
        "status": "success",
        "data": {
            "latest": latest,
            "history": history,
            "fitness": fitness,
            "alerts": alerts,
            "achievements": achievements
        }
    }