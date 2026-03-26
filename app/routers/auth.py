from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase

from pydantic import BaseModel, EmailStr
import os

router = APIRouter(prefix="/api/v1", tags=["Auth"])

@router.get("/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    resp = (
        sb.table("profiles")
        .select("user_id, role, full_name")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    profile = resp.data[0] if resp.data else None

    return {
        "user_id": user_id,
        "role": profile.get("role") if profile else None,
        "full_name": profile.get("full_name") if profile else None,
    }

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    sb = get_supabase()

    redirect_to = os.getenv(
        "PASSWORD_RESET_REDIRECT_URL",
        "https://careminder-backend.onrender.com/reset-password"
    )

    try:
        resp = sb.auth.reset_password_email(
            payload.email,
            {
                "redirect_to": redirect_to
            }
        )
        return {
            "status": "success",
            "message": "Password reset email sent"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

class ResetPasswordRequest(BaseModel):
    new_password: str


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    try:
        sb.auth.update_user({
            "password": payload.new_password
        })

        return {
            "status": "success",
            "message": "Password updated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))    