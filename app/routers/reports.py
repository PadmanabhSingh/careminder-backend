from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
from app.schemas.reports import GenerateSummaryRequest, GenerateReportRequest

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


@router.get("/summaries")
def get_summaries(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    resp = (
        sb.table("daily_summaries")
        .select("*")
        .eq("user_id", user_id)
        .order("summary_date", desc=True)
        .execute()
    )

    return {
        "count": len(resp.data),
        "data": resp.data
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

    resp = (
        sb.table("reports")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "count": len(resp.data),
        "data": resp.data
    }