from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
from app.schemas.appointments import CreateAppointmentRequest, UpdateAppointmentRequest
from datetime import date, datetime 

router = APIRouter(
    prefix="/api/v1/appointments",
    tags=["Appointments"]
)


@router.post("")
def create_appointment(
    payload: CreateAppointmentRequest,
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    if payload.date < date.today():
        raise HTTPException(status_code=400, detail="Appointment date must be today or in the future")

    specialist_resp = (
        sb.table("specialists")
        .select("*")
        .eq("id", payload.specialist_id)
        .limit(1)
        .execute()
    )

    if not specialist_resp.data:
        raise HTTPException(status_code=404, detail="Specialist not found")

    specialist = specialist_resp.data[0]

    slot_resp = (
        sb.table("specialist_availability")
        .select("*")
        .eq("specialist_id", payload.specialist_id)
        .eq("available_date", str(payload.date))
        .eq("time_slot", payload.time)
        .eq("is_booked", False)
        .limit(1)
        .execute()
    )

    if not slot_resp.data:
        raise HTTPException(status_code=409, detail="Selected time slot is not available")

    appointment_data = {
        "user_id": user_id,
        "specialist_id": payload.specialist_id,
        "appointment_date": str(payload.date),
        "appointment_time": payload.time,
        "location": payload.location,
        "status": "confirmed"
    }

    created = sb.table("appointments").insert(appointment_data).execute()

    if not getattr(created, "data", None):
        raise HTTPException(status_code=500, detail="Failed to create appointment")

    sb.table("specialist_availability").update({
        "is_booked": True
    }).eq("specialist_id", payload.specialist_id) \
     .eq("available_date", str(payload.date)) \
     .eq("time_slot", payload.time) \
     .execute()

    row = created.data[0]

    return {
        "status": "success",
        "data": {
            "id": row["id"],
            "doctorName": specialist["name"],
            "specialty": specialist["specialty"],
            "date": row["appointment_date"],
            "time": row["appointment_time"],
            "location": row["location"],
            "status": row["status"],
            "imagePath": specialist["image_path"]
        }
    }


@router.get("")
def get_appointments(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

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


@router.patch("/{id}")
def update_appointment(
    id: str,
    payload: UpdateAppointmentRequest,
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    existing_resp = (
        sb.table("appointments")
        .select("*")
        .eq("id", id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not existing_resp.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    existing = existing_resp.data[0]

    update_data = {}

    if payload.status is not None:
        update_data["status"] = payload.status

    if payload.date is not None:
        update_data["appointment_date"] = payload.date

    if payload.time is not None:
        update_data["appointment_time"] = payload.time

    if payload.location is not None:
        update_data["location"] = payload.location

    if not update_data:
        return {
            "status": "success",
            "message": "No changes applied",
            "data": existing
        }

    updated = (
        sb.table("appointments")
        .update(update_data)
        .eq("id", id)
        .eq("user_id", user_id)
        .execute()
    )

    if not getattr(updated, "data", None):
        raise HTTPException(status_code=500, detail="Failed to update appointment")

    return {
        "status": "success",
        "data": updated.data[0]
    }


@router.get("/{id}/notes")
def get_appointment_notes(id: str, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    appt_resp = (
        sb.table("appointments")
        .select("*")
        .eq("id", id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not appt_resp.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    note_resp = (
        sb.table("appointment_notes")
        .select("*")
        .eq("appointment_id", id)
        .limit(1)
        .execute()
    )

    if not note_resp.data:
        return {
            "status": "success",
            "data": None
        }

    return {
        "status": "success",
        "data": note_resp.data[0]
    }