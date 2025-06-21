from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from openai import OpenAI
import os

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=api_key) if api_key else None

# FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to https://app.gateofai.com in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend expects 'message' and 'data'
class SmartChatRequest(BaseModel):
    message: str
    data: list[dict] = []

@app.post("/chat")
async def chat_with_data(payload: SmartChatRequest):
    if not client:
        return {"reply": "❌ OPENAI_API_KEY not set on server."}

    try:
        df_summary = ""
        if payload.data:
            df = pd.DataFrame(payload.data)
            summary = df.describe(include='all').to_string()
            df_summary = f"\n\nPreview (first 5 rows):\n{df.head().to_string()}\n\nSummary:\n{summary}"

        prompt = f"{df_summary}\n\nQuestion: {payload.message}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst who answers questions about tabular data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()
        return {"reply": reply}

    except Exception as e:
        return {"reply": f"❌ Server error: {str(e)}"}
