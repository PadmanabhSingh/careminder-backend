from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from fastapi.responses import JSONResponse 

load_dotenv(".env")

router = APIRouter(
    prefix="/api/v1/integrations/withings",
    tags=["Withings Integration"]
)


def get_withings_config():
    client_id = os.getenv("WITHINGS_CLIENT_ID")
    client_secret = os.getenv("WITHINGS_CLIENT_SECRET")
    redirect_uri = os.getenv("WITHINGS_REDIRECT_URI")
    api_base = os.getenv("WITHINGS_API_BASE", "https://wbsapi.withings.net")

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=500, detail="Missing Withings environment variables")

    return client_id, client_secret, redirect_uri, api_base


@router.get("/auth-url")
def get_withings_auth_url(user_id: str = Depends(get_current_user_id)):
    client_id, _, redirect_uri, _ = get_withings_config()

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "user.metrics,user.activity",
        "state": user_id
    }

    auth_url = f"https://account.withings.com/oauth2_user/authorize2?{urlencode(params)}"

    return {
        "status": "success",
        "data": {
            "auth_url": auth_url
        }
    }

@router.api_route("/callback", methods=["GET", "POST", "HEAD"])
async def withings_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None)
):
    if request.method == "HEAD":
        return JSONResponse(status_code=200, content={})

    if not code or not state:
        return {
            "status": "callback_ready",
            "method": request.method,
            "message": "Withings callback endpoint is reachable"
        }

    client_id, client_secret, redirect_uri, api_base = get_withings_config()
    sb = get_supabase()

    token_url = f"{api_base}/v2/oauth2"

    payload = {
        "action": "requesttoken",
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    resp = requests.post(token_url, data=payload, timeout=20)
    data = resp.json()

    if resp.status_code != 200 or "body" not in data:
        raise HTTPException(status_code=400, detail=f"Withings token exchange failed: {data}")

    body = data["body"]

    save_data = {
        "user_id": state,
        "withings_user_id": str(body.get("userid")),
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
        "expires_in": body.get("expires_in"),
        "scope": body.get("scope"),
        "token_type": body.get("token_type"),
    }

    saved = sb.table("withings_tokens").upsert(save_data).execute()

    if not getattr(saved, "data", None):
        raise HTTPException(status_code=500, detail="Failed to save Withings tokens")

    return {
        "status": "connected",
        "data": saved.data[0]
    }

@router.post("/sync")
def sync_withings_data(user_id: str = Depends(get_current_user_id)):
    _, _, _, api_base = get_withings_config()
    sb = get_supabase()

    token_resp = (
        sb.table("withings_tokens")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    token_rows = token_resp.data or []
    if not token_rows:
        raise HTTPException(status_code=404, detail="No Withings connection found for this user")

    token_row = token_rows[0]
    access_token = token_row["access_token"]

    meas_url = f"{api_base}/measure"

    params = {
        "action": "getmeas"
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    resp = requests.get(meas_url, params=params, headers=headers, timeout=20)
    data = resp.json()

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Withings sync failed: {data}")

    measures = data.get("body", {}).get("measuregrps", [])

    inserted = []

    for grp in measures[:10]:
        date_epoch = grp.get("date")
        measured_at = None

        if date_epoch:
            from datetime import datetime, timezone
            measured_at = datetime.fromtimestamp(date_epoch, tz=timezone.utc).isoformat()

        for m in grp.get("measures", []):
            type_code = m.get("type")
            value = m.get("value")
            unit_exp = m.get("unit", 0)

            if value is None:
                continue

            actual_value = value * (10 ** unit_exp)

            biomarker_type = None
            biomarker_unit = None
                        # Type 4 = height (meters from Withings scale)
            if type_code == 4:
                height_cm = actual_value * 100

                sb.table("profiles").update({
                    "height_cm": height_cm
                }).eq("user_id", user_id).execute()

                inserted.append({
                    "kind": "profile_update",
                    "field": "height_cm",
                    "value": height_cm
                })
                continue
            
            if type_code == 9:
                biomarker_type = "blood_pressure_diastolic"
                biomarker_unit = "mmHg"
            elif type_code == 10:
                biomarker_type = "blood_pressure_systolic"
                biomarker_unit = "mmHg"
            elif type_code == 11:
                biomarker_type = "heart_rate"
                biomarker_unit = "bpm"

            if not biomarker_type:
                continue

            row = {
                "user_id": user_id,
                "type": biomarker_type,
                "value": actual_value,
                "unit": biomarker_unit,
                "recorded_at": measured_at,
            }

            saved = sb.table("biomarker_readings").insert(row).execute()
            if getattr(saved, "data", None):
                inserted.append(saved.data[0])

    return {
        "status": "synced",
        "count": len(inserted),
        "data": inserted,
        "raw_measure_groups_count": len(measures),
        "raw_measure_groups": measures[:3]
    }
