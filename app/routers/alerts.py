from fastapi import APIRouter, HTTPException, Query
from app.db.supabase import get_supabase
from app.schemas.alerts import ThresholdRequest

router = APIRouter(
    prefix="/api/v1",
    tags=["Alerts & Thresholds"]
)


@router.post("/thresholds")
def create_threshold(payload: ThresholdRequest):
    sb = get_supabase()

    data_to_insert = {
        "user_id": str(payload.user_id),
        "type": payload.type,
        "min_value": payload.min_value,
        "max_value": payload.max_value,
        "severity": payload.severity,
    }

    resp = sb.table("health_thresholds").upsert(
        data_to_insert,
        on_conflict="user_id,type"
    ).execute()

    if not getattr(resp, "data", None):
        raise HTTPException(status_code=500, detail="Failed to save threshold")

    return {
        "status": "saved",
        "data": resp.data[0]
    }


@router.get("/alerts")
def get_alerts(user_id: str = Query(...)):
    sb = get_supabase()

    resp = (
        sb.table("alerts")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "count": len(resp.data),
        "data": resp.data
    }