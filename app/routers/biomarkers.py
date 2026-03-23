from fastapi import APIRouter, Query, HTTPException
from app.db.supabase import get_supabase
from app.schemas.biomarkers import BiomarkerIngestRequest
import traceback
from fastapi import Depends
from app.core.auth import get_current_user_id
from datetime import datetime , date , timedelta, timezone 
from collections import defaultdict

router = APIRouter(
    prefix="/api/v1/biomarkers",
    tags=["Biomarkers"]
)


@router.post("/ingest")
def ingest_biomarker(payload: BiomarkerIngestRequest):
    sb = get_supabase()

    try:
        data_to_insert = {
            "user_id": str(payload.user_id),
            "type": payload.type,
            "value": payload.value,
            "unit": payload.unit,
            "recorded_at": payload.recorded_at.isoformat()
        }

        resp = sb.table("biomarker_readings").insert(data_to_insert).execute()

        if not getattr(resp, "data", None):
            raise HTTPException(status_code=500, detail="Failed to save biomarker reading")

        saved_reading = resp.data[0]

        threshold_resp = (
            sb.table("health_thresholds")
            .select("*")
            .eq("user_id", str(payload.user_id))
            .eq("type", payload.type)
            .limit(1)
            .execute()
        )

        threshold_data = threshold_resp.data or []

        if threshold_data:
            threshold = threshold_data[0]
            min_value = threshold.get("min_value")
            max_value = threshold.get("max_value")
            severity = threshold.get("severity", "medium")

            is_alert = False
            message = None

            if min_value is not None and payload.value < float(min_value):
                is_alert = True
                message = f"{payload.type} below minimum threshold"
            elif max_value is not None and payload.value > float(max_value):
                is_alert = True
                message = f"{payload.type} above maximum threshold"

            if is_alert:
                alert_data = {
                    "user_id": str(payload.user_id),
                    "type": payload.type,
                    "reading_id": saved_reading["id"],
                    "severity": severity,
                    "message": message
                }

                sb.table("alerts").insert(alert_data).execute()

        return {
            "status": "saved",
            "data": saved_reading
        }

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR in /ingest:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest/mine")
def get_my_latest_biomarker_for_date(
    date_param: date = Query(..., alias="date", description="Date in YYYY-MM-DD"),
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    start_dt = datetime.combine(date_param, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)

    resp = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .gte("recorded_at", start_dt.isoformat())
        .lt("recorded_at", end_dt.isoformat())
        .order("recorded_at", desc=True)
        .execute()
    )

    rows = resp.data or []

    latest = {
        "heartRate": None,
        "systolicBP": None,
        "diastolicBP": None,
        "glucose": None,
        "oxygen": None,
        "sleepHours": None,
        "stressLevel": None,
        "date": date_param.isoformat()
    }

    for row in rows:
        biomarker_type = row.get("type")
        value = row.get("value")

        if biomarker_type == "heart_rate" and latest["heart_rate"] is None:
            latest["heart_rate"] = float(value)
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

    return {
        "status": "success",
        "data": latest
    }


@router.get("/history/mine")
def get_my_biomarker_history(
    days: int = Query(7, ge=1, le=365, description="Number of days of history"),
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    resp = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .gte("recorded_at", start_dt.isoformat())
        .lt("recorded_at", end_dt.isoformat())
        .order("recorded_at", desc=False)
        .execute()
    )

    rows = resp.data or []

    day_index = {}
    date_list = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        iso_d = d.isoformat()
        day_index[iso_d] = i
        date_list.append(iso_d)

    history = {
        "dates": date_list,
        "weeklyHeartRate": [None] * days,
        "weeklySystolic": [None] * days,
        "weeklyDiastolic": [None] * days,
        "weeklyGlucose": [None] * days,
        "weeklyOxygen": [None] * days,
        "weeklySleep": [None] * days,
        "weeklyStress": [None] * days
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

    return {
        "status": "success",
        "days": days,
        "data": history
    }

@router.get("")
def get_biomarkers(
    user_id: str = Query(..., description="User UUID"),
    biomarker_type: str | None = Query(None, description="Optional biomarker type")
):
    sb = get_supabase()

    query = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .order("recorded_at", desc=True)
    )

    if biomarker_type:
        query = query.eq("type", biomarker_type)

    resp = query.execute()

    return {
        "count": len(resp.data),
        "data": resp.data
    }


@router.get("/latest")
def get_latest_biomarker(
    user_id: str = Query(..., description="User UUID"),
    biomarker_type: str = Query(..., description="biomarker type e.g. heart_rate"),
):
    sb = get_supabase()

    resp = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .eq("type", biomarker_type)
        .order("recorded_at", desc=True)
        .limit(1)
        .execute()
    )

    data = resp.data or []
    if not data:
        raise HTTPException(status_code=404, detail="No biomarker data found")

    return data[0]

@router.get("/mine")
def get_my_biomarkers(
    biomarker_type: str | None = Query(None, description="Optional biomarker type"),
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    query = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .order("recorded_at", desc=True)
    )

    if biomarker_type:
        query = query.eq("type", biomarker_type)

    resp = query.execute()

    return {
        "count": len(resp.data),
        "data": resp.data
    }

