from fastapi import APIRouter, Query, HTTPException
from app.db.supabase import get_supabase
from app.schemas.biomarkers import BiomarkerIngestRequest
import traceback

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