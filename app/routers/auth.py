from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
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

