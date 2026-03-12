from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:

    token = credentials.credentials

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        return user_id

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")