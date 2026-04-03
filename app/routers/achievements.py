from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.db.supabase import get_supabase
from app.schemas.achievements import ShareAchievementRequest

router = APIRouter(
    prefix="/api/v1/achievements",
    tags=["Achievements"]
)


@router.get("/achievements")
def get_achievements(user_id: str = Depends(get_current_user_id)):
    sb = get_supabase()

    resp = (
        sb.table("achievements")
        .select("*")
        .eq("user_id", user_id)
        .order("achieved_at", desc=True)
        .execute()
    )

    rows = resp.data or []

    formatted = [
        {
            "id": row["id"],
            "title": row.get("title", ""),
            "description": row.get("description", ""),
            "date": str(row.get("achieved_at", ""))[:10] if row.get("achieved_at") else "",
            "icon_name": row.get("icon_name", "default"),
            "bg_color_hex": row.get("bg_color_hex", "0xFFD1E9FF"),
            "icon_color_hex": row.get("icon_color_hex", "0xFF1A1F71"),
        }
        for row in rows
    ]

    return {
        "stats": {
            "total": len(formatted)
        },
        "list": formatted
    }


@router.post("/{id}/share")
def share_achievement(
    id: str,
    payload: ShareAchievementRequest,
    user_id: str = Depends(get_current_user_id)
):
    sb = get_supabase()

    ach_resp = (
        sb.table("achievements")
        .select("*")
        .eq("id", id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not ach_resp.data:
        raise HTTPException(status_code=404, detail="Achievement not found")

    share_resp = (
        sb.table("achievement_shares")
        .select("*")
        .eq("achievement_id", id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    deep_link = f"careminder://achievement/{id}"

    if share_resp.data:
        current = share_resp.data[0]
        new_count = current["share_count"] + 1

        updated = (
            sb.table("achievement_shares")
            .update({
                "share_count": new_count
            })
            .eq("achievement_id", id)
            .eq("user_id", user_id)
            .execute()
        )

        data = updated.data[0] if updated.data else current
    else:
        created = (
            sb.table("achievement_shares")
            .insert({
                "achievement_id": id,
                "user_id": user_id,
                "share_count": 1
            })
            .execute()
        )
        data = created.data[0] if created.data else None

    return {
        "status": "success",
        "share": data,
        "deep_link": deep_link
    }