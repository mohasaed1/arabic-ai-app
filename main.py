from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from openai import OpenAI
import os

# Initialize OpenAI client with secure environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY is not set in environment variables.")

client = OpenAI(api_key=api_key)

# FastAPI app
app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request payload model
class QueryPayload(BaseModel):
    message: str
    data: list[dict] = []

# Chat endpoint
@app.post("/chat")
async def chat_with_data(payload: QueryPayload):
    try:
        # Data summary (if provided)
        df_summary = ""
        if payload.data:
            df = pd.DataFrame(payload.data)
            summary = df.describe(include='all').to_string()
            df_summary = f"Here is the data summary:\n{summary}"

        prompt = f"You are a helpful data analyst.\n{df_summary}\n\nUser question: {payload.message}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful data assistant. Answer clearly and directly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"❌ Server error: {str(e)}"}
