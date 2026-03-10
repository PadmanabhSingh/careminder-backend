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

        return {
            "status": "saved",
            "data": resp.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR in /ingest:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))