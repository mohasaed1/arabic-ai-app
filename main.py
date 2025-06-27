from routes.upload_file import router as upload_file_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from openai import OpenAI
import os

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.gateofai.com"]
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            numeric_cols = df.select_dtypes(include='number').columns

            stats = df[numeric_cols].agg(['sum', 'mean', 'min', 'max']).to_string() if not numeric_cols.empty else "No numeric data available."
            preview = df.head().to_string(index=False)

            df_summary = f"🔎 Preview (first 5 rows):\n{preview}\n\n📊 Numeric Summary (sum, avg, min, max):\n{stats}"

        lang = "ar" if any('\u0600' <= char <= '\u06FF' for char in payload.message) else "en"
        prompt = f"{df_summary}\n\n📥 Question:\n{payload.message}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a multilingual data analyst who answers questions based on tables, supporting Arabic and English. Always compute totals or summaries when requested."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()
        return {"reply": reply}

    except Exception as e:
        return {"reply": f"❌ Server error: {str(e)}"}

app.include_router(upload_file_router)
