import os
from fastapi import APIRouter, Depends, HTTPException
from dotenv import load_dotenv
from openai import OpenAI

from app.core.auth import get_current_user_id
from app.schemas.chat import ChatRequest

load_dotenv(".env")

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["AI Chat"]
)


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


@router.post("")
def chat_with_ai(
    payload: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    try:
        client = get_openai_client()

        response = client.responses.create(
            model="gpt-5",
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a supportive health companion assistant for CareMinder. "
                        "You can explain general wellness information and help users understand "
                        "their health data in simple language. "
                        "Do not claim to diagnose diseases. "
                        "If symptoms sound urgent or severe, advise the user to seek professional care."
                    ),
                },
                {
                    "role": "user",
                    "content": payload.message,
                },
            ],
        )

        return {
            "status": "success",
            "data": {
                "reply": response.output_text
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))