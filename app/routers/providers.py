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
        .limit(1)
        .execute()
    )

    if not role_resp.data:
        raise HTTPException(status_code=404, detail="Provider profile not found")

    role = role_resp.data[0].get("role")
    if role != "provider":
        raise HTTPException(status_code=403, detail="User is not a provider")


def can_access_patient(sb, provider_id: str, user_id: str) -> bool:
    perm_resp = (
        sb.table("provider_permissions")
        .select("*")
        .eq("provider_id", provider_id)
        .eq("user_id", user_id)
        .is_("revoked_at", None)
        .limit(1)
        .execute()
    )
    return bool(perm_resp.data)

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

@router.get("/patient/{user_id}/summaries")
def get_patient_summaries(user_id: str, provider_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    ensure_provider(sb, provider_id)

    if not can_access_patient(sb, provider_id, user_id):
        raise HTTPException(status_code=403, detail="Access denied to this patient")

    resp = (
        sb.table("daily_summaries")
        .select("*")
        .eq("user_id", user_id)
        .order("summary_date", desc=True)
        .execute()
    )

    summaries = resp.data or []

    return {
        "status": "success",
        "count": len(summaries),
        "data": summaries
    }

@router.get("/appointments")
def get_provider_all_appointments(provider_id: str = Depends(get_current_user_id)):
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
        return {
            "status": "success",
            "count": 0,
            "data": []
        }

    appt_resp = (
        sb.table("appointments")
        .select("*")
        .in_("user_id", patient_ids)
        .order("appointment_date", desc=False)
        .execute()
    )

    appointments = appt_resp.data or []
    result = []

    for appt in appointments:
        profile_resp = (
            sb.table("profiles")
            .select("first_name,last_name,full_name")
            .eq("user_id", appt["user_id"])
            .limit(1)
            .execute()
)
        patient = profile_resp.data[0] if profile_resp.data else {"first_name": "","last_name": "","full_name": "Unknown Patient"}

        spec_resp = (
            sb.table("specialists")
            .select("*")
            .eq("id", appt["specialist_id"])
            .limit(1)
            .execute()
        )
        specialist = spec_resp.data[0] if spec_resp.data else {
            "name": "Unknown Specialist",
            "specialty": "",
            "image_path": ""
        }

        first_name = patient.get("first_name", "")
        last_name = patient.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or patient.get("full_name", "Unknown Patient")

    result.append({
        "id": appt["id"],
        "patientId": appt["user_id"],
        "firstName": first_name,
        "lastName": last_name,
        "fullName": full_name,
        "patientName": full_name,
        "doctorName": specialist["name"],
        "specialty": specialist["specialty"],
        "date": appt["appointment_date"],
        "time": appt["appointment_time"],
        "location": appt["location"],
        "status": appt["status"],
        "imagePath": specialist["image_path"]
})

    return {
        "status": "success",
        "count": len(result),
        "data": result
    }

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
        return {"status": "success", "count": 0, "data": []}

    profiles_resp = (
    sb.table("profiles")
    .select("user_id, first_name, last_name, full_name, role, date_of_birth, gender, height_cm, weight_kg")
    .in_("user_id", patient_ids)
    .execute()
)

    return {
        "status": "success",
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
@router.get("/patient/{user_id}/reports")
def get_patient_reports(user_id: str, provider_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    ensure_provider(sb, provider_id)

    if not can_access_patient(sb, provider_id, user_id):
        raise HTTPException(status_code=403, detail="Access denied to this patient")

    resp = (
        sb.table("reports")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    reports = resp.data or []

    return {
        "status": "success",
        "count": len(reports),
        "data": reports
    }

@router.get("/patient/{user_id}/appointments")
def get_patient_appointments(user_id: str, provider_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    ensure_provider(sb, provider_id)

    if not can_access_patient(sb, provider_id, user_id):
        raise HTTPException(status_code=403, detail="Access denied to this patient")

    resp = (
        sb.table("appointments")
        .select("*")
        .eq("user_id", user_id)
        .order("appointment_date", desc=False)
        .execute()
    )

    appointments = resp.data or []
    result = []

    for appt in appointments:
        spec_resp = (
            sb.table("specialists")
            .select("*")
            .eq("id", appt["specialist_id"])
            .limit(1)
            .execute()
        )

        specialist = spec_resp.data[0] if spec_resp.data else {
            "name": "Unknown Specialist",
            "specialty": "",
            "image_path": ""
        }

        result.append({
            "id": appt["id"],
            "doctorName": specialist["name"],
            "specialty": specialist["specialty"],
            "date": appt["appointment_date"],
            "time": appt["appointment_time"],
            "location": appt["location"],
            "status": appt["status"],
            "imagePath": specialist["image_path"]
        })

    return {
        "status": "success",
        "count": len(result),
        "data": result
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

    