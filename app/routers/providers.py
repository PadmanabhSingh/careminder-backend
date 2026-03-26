from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
from app.schemas.providers import ClinicalNoteRequest

router = APIRouter(
    prefix="/api/v1/provider",
    tags=["Provider Dashboard"]
)


def ensure_provider(sb, provider_id: str):
    role_resp = (
        sb.table("profiles")
        .select("role")
        .eq("user_id", provider_id)
        .eq("role", "provider")
        .limit(1)
        .execute()
    )

    if not role_resp.data:
        raise HTTPException(status_code=404, detail="Provider profile not found")

    role = role_resp.data[0].get("role")
    if role != "provider":
        raise HTTPException(status_code=403, detail="User is not a provider")


def ensure_provider_can_access(sb, provider_id: str, patient_id: str):
    perm_resp = (
        sb.table("provider_permissions")
        .select("*")
        .eq("provider_id", provider_id)
        .eq("user_id", patient_id)
        .is_("revoked_at", None)
        .limit(1)
        .execute()
    )

    if not perm_resp.data:
        raise HTTPException(status_code=403, detail="Provider does not have access to this patient")


@router.get("/patients")
def get_provider_patients(provider_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    ensure_provider(sb, provider_id)

    perm_resp = (
        sb.table("provider_permissions")
        .select("user_id")
        .eq("provider_id", provider_id)
        .is_("revoked_at", None)
        .execute()
    )

    patient_ids = [row["user_id"] for row in (perm_resp.data or [])]

    if not patient_ids:
        return {"count": 0, "data": []}

    profiles_resp = (
        sb.table("profiles")
        .select("*")
        .in_("user_id", patient_ids)
        .execute()
    )

    return {
        "count": len(profiles_resp.data),
        "data": profiles_resp.data
    }


@router.get("/patient/{user_id}/biomarkers")
def get_patient_biomarkers(user_id: str, provider_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    ensure_provider(sb, provider_id)
    ensure_provider_can_access(sb, provider_id, user_id)

    resp = (
        sb.table("biomarker_readings")
        .select("*")
        .eq("user_id", user_id)
        .order("recorded_at", desc=True)
        .execute()
    )

    return {
        "count": len(resp.data),
        "data": resp.data
    }


@router.get("/patient/{user_id}/alerts")
def get_patient_alerts(user_id: str, provider_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    ensure_provider(sb, provider_id)
    ensure_provider_can_access(sb, provider_id, user_id)

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


@router.get("/patient/{user_id}/notes")
def get_patient_notes(user_id: str, provider_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    ensure_provider(sb, provider_id)
    ensure_provider_can_access(sb, provider_id, user_id)

    resp = (
        sb.table("clinical_notes")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "count": len(resp.data),
        "data": resp.data
    }


@router.post("/clinical-notes")
def create_clinical_note(
    payload: ClinicalNoteRequest,
    provider_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    ensure_provider(sb, provider_id)
    ensure_provider_can_access(sb, provider_id, str(payload.user_id))

    data_to_insert = {
        "user_id": str(payload.user_id),
        "provider_id": provider_id,
        "note": payload.note
    }

    resp = sb.table("clinical_notes").insert(data_to_insert).execute()

    if not getattr(resp, "data", None):
        raise HTTPException(status_code=500, detail="Failed to create clinical note")

    return {
        "status": "saved",
        "data": resp.data[0]
    }