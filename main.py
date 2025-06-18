from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
from openai import OpenAI

# Ensure the API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY is not set in environment variables.")

# Initialize OpenAI client with API key
client = OpenAI(api_key=api_key)

# Initialize FastAPI
app = FastAPI()

# Enable CORS for all origins (adjust for security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["https://app.gateofai.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class QueryPayload(BaseModel):
    message: str
    data: list[dict] = []

@app.post("/chat")
async def chat_with_data(payload: QueryPayload):
    try:
        df_summary = ""
        if payload.data:
            df = pd.DataFrame(payload.data)
            summary = df.describe(include="all").to_string()
            df_summary = f"Here is a summary of your data:\n{summary}"

        prompt = f"You are a helpful data analyst.\n{df_summary}\n\nUser question: {payload.message}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful data assistant. Answer clearly and directly."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        reply = response.choices[0].message.content.strip()
        return {"reply": reply}

    except Exception as e:
        print("❌ Error in /chat:", str(e))
        return {"reply": f"❌ Server error: {str(e)}"}
