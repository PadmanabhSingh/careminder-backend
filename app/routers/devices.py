from fastapi import APIRouter, HTTPException, Depends
from app.db.supabase import get_supabase
from app.schemas.devices import DeviceRegisterRequest, DeviceIngestRequest
from app.core.auth import get_current_user_id
from datetime import datetime, timezone

router = APIRouter(
    prefix="/api/v1/devices",
    tags=["Devices"]
)

VALID_DEVICE_TYPES = [
    "Smart Watch",
    "Blood Pressure Monitor",
    "Glucose Meter",
    "Thermometer",
]


@router.get("")
def get_my_devices(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    resp = (
        sb.table("devices")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "status": "success",
        "count": len(resp.data),
        "data": resp.data
    }


@router.post("/register")
def register_device(payload: DeviceRegisterRequest):
    sb = get_supabase()

    if payload.device_type not in VALID_DEVICE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid device_type. Allowed values: {VALID_DEVICE_TYPES}"
        )

    # Prevent duplicate device name for same user
    existing = (
        sb.table("devices")
        .select("*")
        .eq("user_id", str(payload.user_id))
        .eq("device_name", payload.device_name)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise HTTPException(
            status_code=409,
            detail="Device with the same name already exists for this user"
        )

    data_to_insert = {
        "user_id": str(payload.user_id),
        "device_name": payload.device_name,
        "vendor": payload.vendor,
        "model": payload.model,
        "status": payload.status,
        "battery_percent": payload.battery_percent,
        "device_type": payload.device_type,
    }

    resp = sb.table("devices").insert(data_to_insert).execute()

    if not getattr(resp, "data", None):
        raise HTTPException(status_code=500, detail="Failed to register device")

    return {
        "status": "registered",
        "data": resp.data[0]
    }


@router.delete("/{device_id}")
def delete_device(device_id: str, user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    existing = (
        sb.table("devices")
        .select("*")
        .eq("id", device_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Device not found")

    sb.table("devices").delete().eq("id", device_id).eq("user_id", user_id).execute()

    return {
        "status": "success",
        "message": "Device deleted"
    }


def normalize_device_payload(vendor: str, payload: dict):
    vendor = vendor.lower()

    if vendor == "apple_watch":
        return {
            "type": "heart_rate",
            "value": payload["heart_rate"],
            "unit": "bpm",
            "recorded_at": payload.get("timestamp", datetime.now(timezone.utc).isoformat())
        }

    elif vendor == "withings":
        return {
            "type": "blood_pressure_systolic",
            "value": payload["systolic"],
            "unit": "mmHg",
            "recorded_at": payload.get("timestamp", datetime.now(timezone.utc).isoformat())
        }

    elif vendor == "dexcom":
        return {
            "type": "blood_glucose",
            "value": payload["glucose_value"],
            "unit": "mg/dL",
            "recorded_at": payload.get("timestamp", datetime.now(timezone.utc).isoformat())
        }

    elif vendor == "simulator":
        return {
            "type": payload["type"],
            "value": payload["value"],
            "unit": payload.get("unit", ""),
            "recorded_at": payload.get("recorded_at", datetime.now(timezone.utc).isoformat())
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported vendor: {vendor}")


@router.post("/ingest-json")
def ingest_device_json(payload: DeviceIngestRequest):
    sb = get_supabase()

    normalized = normalize_device_payload(payload.vendor, payload.payload)

    data_to_insert = {
        "user_id": str(payload.user_id),
        "device_id": str(payload.device_id) if payload.device_id else None,
        "type": normalized["type"],
        "value": normalized["value"],
        "unit": normalized["unit"],
        "recorded_at": normalized["recorded_at"],
    }

    resp = sb.table("biomarker_readings").insert(data_to_insert).execute()

    if not getattr(resp, "data", None):
        raise HTTPException(status_code=500, detail="Failed to ingest device data")

    return {
        "status": "ingested",
        "normalized_data": normalized,
        "saved_data": resp.data[0]
    }