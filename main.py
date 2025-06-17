from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
from openai import OpenAI

# ✅ Initialize OpenAI client correctly
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ FastAPI app
app = FastAPI()

# ✅ Allow CORS (needed for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Input model for POST requests
class QueryPayload(BaseModel):
    message: str
    data: list[dict] = []

# ✅ Chat endpoint
@app.post("/chat")
async def chat_with_data(payload: QueryPayload):
    try:
        df_summary = ""

        # Optional: summarize data if included
        if payload.data:
            df = pd.DataFrame(payload.data)
            summary = df.describe(include="all").to_string()
            df_summary = f"Here is the data summary:\n{summary}"

        # Full prompt
        prompt = f"You are a helpful data analyst.\n{df_summary}\n\nUser question: {payload.message}"

        # OpenAI API call (new SDK format)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful data assistant. Answer clearly and directly."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        # Extract reply
        reply = response.choices[0].message.content.strip()
        return {"reply": reply}

    except Exception as e:
        # Useful for Railway logs
        print("Error in /chat endpoint:", str(e))
        return {"reply": f"❌ Server error: {str(e)}"}
