from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

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
    client_id, _, redirect_uri, api_base = get_withings_config()

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "user.info,user.metrics",
        "state": user_id
    }

    auth_url = f"{api_base}/oauth2_user/authorize2?{urlencode(params)}"

    return {
        "status": "success",
        "data": {
            "auth_url": auth_url
        }
    }


@router.get("/callback")
def withings_callback(
    code: str | None = Query(None),
    state: str | None = Query(None)
):
    # This lets Withings verify the callback URL without query params
    if not code or not state:
        return {
            "status": "callback_ready",
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