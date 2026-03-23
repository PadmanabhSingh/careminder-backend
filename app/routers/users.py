from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
from app.schemas.users import UserPreferencesUpdateRequest

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


@router.patch("/me/preferences")
def update_my_preferences(
    payload: UserPreferencesUpdateRequest,
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    resp = (
        sb.table("profiles")
        .update({
            "share_data_with_provider": payload.share_data_with_provider,
            "automatic_sync": payload.automatic_sync,
            "low_battery_notifications": payload.low_battery_notifications,
        })
        .eq("user_id", user_id)
        .execute()
    )

    if not getattr(resp, "data", None):
        raise HTTPException(status_code=500, detail="Failed to update preferences")

    return {
        "status": "success",
        "data": resp.data[0]
    }