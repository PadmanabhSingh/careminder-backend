from fastapi import Header, HTTPException
import jwt
import os
from dotenv import load_dotenv

load_dotenv(".env")


def get_current_user_id(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        return user_id

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")