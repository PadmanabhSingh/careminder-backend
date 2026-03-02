from fastapi import APIRouter, Query, HTTPException
from app.db.supabase import get_supabase

router = APIRouter(
    prefix="/api/v1/biomarkers",
    tags=["Biomarkers"]
)

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

    if not resp.data:
        raise HTTPException(status_code=404, detail="No biomarker data found")

    return resp.data[0]