from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import openai
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

class QueryPayload(BaseModel):
    message: str
    data: list[dict] = []

@app.post("/chat")
async def chat_with_data(payload: QueryPayload):
    try:
        df_summary = ""
        if payload.data:
            df = pd.DataFrame(payload.data)
            summary = df.describe(include='all').to_string()
            df_summary = f"Here is the data summary:\n{summary}"

        prompt = f"You are a helpful data analyst.\n{df_summary}\n\nUser question: {payload.message}"

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful data assistant. Answer clearly and directly."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()
        return {"reply": reply}

    except Exception as e:
        print("Error in /chat endpoint:", str(e))  # For Railway logs
        return {"reply": f"❌ Server error: {str(e)}"}
