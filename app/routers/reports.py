from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
from app.schemas.reports import GenerateSummaryRequest, GenerateReportRequest
from datetime import datetime 
router = APIRouter(
    prefix="/api/v1",
    tags=["Summaries & Reports"]
)


@router.post("/summaries/generate")
def generate_summary(
    payload: GenerateSummaryRequest,
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    readings_resp = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .gte("recorded_at", f"{payload.summary_date}T00:00:00+00:00")
        .lt("recorded_at", f"{payload.summary_date}T23:59:59+00:00")
        .order("recorded_at", desc=False)
        .execute()
    )

    readings = readings_resp.data or []

    summary_content = {
        "summary_date": str(payload.summary_date),
        "reading_count": len(readings),
        "biomarkers": readings
    }

    resp = sb.table("daily_summaries").upsert(
        {
            "user_id": user_id,
            "summary_date": str(payload.summary_date),
            "content": summary_content
        },
        on_conflict="user_id,summary_date"
    ).execute()

    if not getattr(resp, "data", None):
        raise HTTPException(status_code=500, detail="Failed to generate summary")

    return {
        "status": "generated",
        "data": resp.data[0]
    }


@router.get("/summaries/latest")
def get_latest_summary(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    resp = (
        sb.table("daily_summaries")
        .select("*")
        .eq("user_id", user_id)
        .order("summary_date", desc=True)
        .limit(1)
        .execute()
    )

    data = resp.data or []
    if not data:
        raise HTTPException(status_code=404, detail="No summaries found")

    return data[0]


@router.get("/summaries/latest")
def get_latest_summary(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    summary_resp = (
        sb.table("daily_summaries")
        .select("*")
        .eq("user_id", user_id)
        .order("summary_date", desc=True)
        .limit(1)
        .execute()
    )

    data = summary_resp.data or []
    if not data:
        raise HTTPException(status_code=404, detail="No summaries found")

    latest_summary = data[0]
    content = latest_summary.get("content", {})
    biomarkers = content.get("biomarkers", [])

    profile_resp = (
        sb.table("profiles")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    profile = (profile_resp.data or [{}])[0]

    vitals = {}
    for row in biomarkers:
        biomarker_type = row.get("biomarker_type")
        value = row.get("value")
        unit = row.get("unit")

        if biomarker_type == "heart_rate":
            vitals["heart_rate"] = f"{value} {unit}"
        elif biomarker_type == "spo2":
            vitals["spo2"] = f"{value} {unit}"
        elif biomarker_type == "blood_pressure_systolic":
            vitals["blood_pressure_systolic"] = f"{value} {unit}"
        elif biomarker_type == "blood_pressure_diastolic":
            vitals["blood_pressure_diastolic"] = f"{value} {unit}"
        elif biomarker_type == "steps":
            vitals["steps"] = value
        elif biomarker_type == "sleep_minutes":
            vitals["sleep_minutes"] = value

    summary_date = latest_summary.get("summary_date")

    return {
        "id": latest_summary.get("id", ""),
        "title": "Daily Health Summary",
        "month": summary_date,
        "generated_at": summary_date,
        "status": "Completed",
        "user_name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
        "user_age": profile.get("age", 0),
        "user_gender": profile.get("gender", ""),
        "past_conditions": profile.get("past_conditions", "None"),
        "allergies": profile.get("allergies", "None"),
        "medications": profile.get("medications", "None"),
        "vitals": vitals
    }


@router.post("/reports/generate")
def generate_report(
    payload: GenerateReportRequest,
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    latest_summary_resp = (
        sb.table("daily_summaries")
        .select("*")
        .eq("user_id", user_id)
        .order("summary_date", desc=True)
        .limit(1)
        .execute()
    )

    latest_summary = (latest_summary_resp.data or [None])[0]

    report_data = {
        "user_id": user_id,
        "generated_by": user_id,
        "title": payload.title,
        "storage_path": None
    }

    resp = sb.table("reports").insert(report_data).execute()

    if not getattr(resp, "data", None):
        raise HTTPException(status_code=500, detail="Failed to generate report")

    return {
        "status": "generated",
        "latest_summary_used": latest_summary,
        "data": resp.data[0]
    }


@router.get("/reports")
def get_reports(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    reports_resp = (
        sb.table("reports")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    profile_resp = (
        sb.table("profiles")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    latest_summary_resp = (
        sb.table("daily_summaries")
        .select("*")
        .eq("user_id", user_id)
        .order("summary_date", desc=True)
        .limit(1)
        .execute()
    )

    profile = (profile_resp.data or [{}])[0]
    latest_summary = (latest_summary_resp.data or [{}])[0]
    summary_content = latest_summary.get("content", {}) if latest_summary else {}
    biomarkers = summary_content.get("biomarkers", [])

    vitals = {}
    for row in biomarkers:
        biomarker_type = row.get("biomarker_type")
        value = row.get("value")
        unit = row.get("unit")

        if biomarker_type == "heart_rate":
            vitals["heart_rate"] = f"{value} {unit}"
        elif biomarker_type == "spo2":
            vitals["spo2"] = f"{value} {unit}"
        elif biomarker_type == "blood_pressure_systolic":
            vitals["blood_pressure_systolic"] = f"{value} {unit}"
        elif biomarker_type == "blood_pressure_diastolic":
            vitals["blood_pressure_diastolic"] = f"{value} {unit}"
        elif biomarker_type == "steps":
            vitals["steps"] = value
        elif biomarker_type == "sleep_minutes":
            vitals["sleep_minutes"] = value

    formatted_reports = []
    for report in reports_resp.data or []:
        created_at = report.get("created_at")
        created_dt = None
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:
                created_dt = None

        formatted_reports.append({
            "id": report.get("id"),
            "title": report.get("title", "Health Report"),
            "month": created_dt.strftime("%B, %Y") if created_dt else "",
            "generated_at": created_at,
            "status": "Completed",
            "user_name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
            "user_age": profile.get("age", 0),
            "user_gender": profile.get("gender", ""),
            "past_conditions": profile.get("past_conditions", "None"),
            "allergies": profile.get("allergies", "None"),
            "medications": profile.get("medications", "None"),
            "vitals": vitals
        })

    return {
        "count": len(formatted_reports),
        "data": formatted_reports
    }