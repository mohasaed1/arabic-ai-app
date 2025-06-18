from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from openai import OpenAI
import os

# Initialize FastAPI app
app = FastAPI()

# Enable CORS (adjust domains as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client using environment variable
client = OpenAI()  # Reads OPENAI_API_KEY from environment

# Pydantic model for request body
class QueryPayload(BaseModel):
    message: str
    data: list[dict] = []

# POST endpoint to handle chat with optional data
@app.post("/chat")
async def chat_with_data(payload: QueryPayload):
    try:
        df_summary = ""
        if payload.data:
            df = pd.DataFrame(payload.data)
            # Remove unsupported describe argument
            summary = df.describe(include="all").to_string()
            df_summary = f"Here is a summary of your data:\n{summary}"

        # Compose full prompt for GPT
        prompt = f"You are a helpful data analyst.\n{df_summary}\n\nUser question: {payload.message}"

        # Request OpenAI chat completion
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
        print("Error:", str(e))
        return {"reply": f"❌ Server error: {str(e)}"}
