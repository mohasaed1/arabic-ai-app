print("🚀 Arabic AI App is starting...")
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
import requests
from openai import OpenAI
import os

app = FastAPI()

# Global variable to hold the OpenAI key
OPENAI_API_KEY = None
client = None

# CORS setup for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["https://app.gateofai.com"] for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch OpenAI key securely from WordPress at startup

@app.on_event("startup")
def fetch_wp_openai_key():
    global OPENAI_API_KEY, client
    try:
        print("🔄 Fetching OpenAI key from WordPress...")
        response = requests.get(
            "https://gateofai.com/wp-json/gateofai/v1/openai-key",
            params={"token": "g8Zx12WvN43pDfK7LmTqY6bP9eAvJrCsXzM0HdQ2"},
            timeout=10
        )
        print("🌐 Response status:", response.status_code)
        print("📦 Response body:", response.text)
        OPENAI_API_KEY = response.json().get("key")

        if OPENAI_API_KEY:
            client = OpenAI(api_key=OPENAI_API_KEY)
            print("✅ Key loaded and OpenAI client initialized.")
        else:
            print("⚠️ Key missing in response.")
    except Exception as e:
        print("❌ Exception during fetch_wp_openai_key:", e)


@app.get("/")
def home():
    return JSONResponse(
        content={"message": "🚀 Arabic AI API is running!"},
        media_type="application/json; charset=utf-8"
    )

@app.post("/analyze")
async def analyze_text(request: Request):
    data = await request.json()
    text = data.get("text", "")

    # Placeholder logic – replace with HuggingFace / CAMeL models later
    return JSONResponse(
        content={
            "summary": "هذا ملخص تجريبي للنص.",
            "sentiment": "محايد",
            "keywords": ["ذكاء", "اصطناعي", "تحليل"]
        },
        media_type="application/json; charset=utf-8"
    )

class AnalysisRequest(BaseModel):
    query: str
    data: List[Dict]

@app.post("/analyze-text")
async def analyze_query(req: AnalysisRequest):
    if "الربح" in req.query and "التكلفة" in req.query:
        ratios = []
        for row in req.data:
            try:
                profit = float(row.get("Revenue", 0)) - float(row.get("Cost", 0))
                cost = float(row.get("Cost", 1))
                ratio = round(profit / cost, 2) if cost else 0
                ratios.append(ratio)
            except:
                continue
        avg_ratio = sum(ratios) / len(ratios) if ratios else 0
        return {"answer": f"🔍 متوسط نسبة الربح إلى التكلفة هو {avg_ratio}"}

    return {"answer": "لم أتمكن من فهم الاستعلام أو حسابه من البيانات الحالية."}

# 🔌 ChatGPT Proxy
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_gpt(req: ChatRequest):
    if not OPENAI_API_KEY:
        return {"error": "API key not loaded."}

        if not client:
        return {"error": "OpenAI client not initialized."}
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": req.message}]
        )

        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}
if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
