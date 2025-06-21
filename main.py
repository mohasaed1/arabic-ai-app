from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from openai import OpenAI
import os

# Initialize OpenAI client with environment variable
api_key = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=api_key) if api_key else None

# FastAPI app
app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    question: str
    data: list[dict] = []
    language: str = "en"

# Chat endpoint
@app.post("/chat-with-data")
async def chat_with_data(payload: ChatRequest):
    if not client:
        return {"answer": "❌ OPENAI_API_KEY not set on server. Please contact admin."}

    try:
        df_summary = ""
        if payload.data:
            df = pd.DataFrame(payload.data)
            summary = df.describe(include='all').to_string()
            df_summary = f"\n\nHere is a preview of the uploaded data (first 5 rows):\n{df.head().to_string()}\n\nSummary:\n{summary}"

        if payload.language == "ar":
            prompt = f"الرجاء تحليل البيانات التالية والإجابة عن السؤال: {payload.question}.{df_summary}"
        else:
            prompt = f"Please analyze the following data and answer the question: {payload.question}.{df_summary}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst who can answer questions about tabular data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        answer = response.choices[0].message.content.strip()
        return {"answer": answer}

    except Exception as e:
        return {"answer": f"❌ Server error: {str(e)}"}
