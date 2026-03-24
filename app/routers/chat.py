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
                        "You are a helpful health companion assistant for CareMinder. "
                        "Give supportive, non-diagnostic guidance. "
                        "Encourage the user to seek professional care for emergencies or serious symptoms,additionally only give response about cardiovascular health."
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