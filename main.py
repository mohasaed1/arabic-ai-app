from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
from openai import OpenAI
import requests
import os
import json

# ✅ Globals
OPENAI_API_KEY = None
client = None

# ✅ App init
app = FastAPI()

# ✅ CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        key = response.json().get("key")
        print("🔑 Loaded API key from WP:", key)

        if key:
            OPENAI_API_KEY = key
            client = OpenAI(api_key=OPENAI_API_KEY)
            print("✅ OpenAI client initialized.")
        else:
            print("⚠️ No key found in response.")
    except Exception as e:
        print("❌ Error loading key:", e)

@app.get("/")
def home():
    return JSONResponse(content={"message": "🚀 Arabic AI API is running!"})

@app.get("/debug-key")
def debug_key():
    return {
        "key_loaded": bool(OPENAI_API_KEY),
        "client_initialized": bool(client)
    }

class AnalysisRequest(BaseModel):
    query: str
    data: List[Dict]

@app.post("/analyze-text")
async def analyze_query(req: AnalysisRequest):
    if not client:
        return {"error": "OpenAI client not initialized."}

    try:
        prompt = (
            "أنت مساعد تحليل بيانات ذكي. ستتلقى استفسار المستخدم وجدول بيانات جزئي (أول 5 صفوف). "
            "قم بتحليل البيانات، أجرِ الحسابات المطلوبة إن أمكن، وقدم شرحًا واضحًا بالاعتماد على البيانات."
        )

        user_input = f"سؤال المستخدم: {req.query}\n\nبيانات المستخدم (صفوف معاينة):\n{json.dumps(req.data[:5], ensure_ascii=False)}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ]
        )

        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

@app.post("/chat")
async def chat_with_gpt(request: Request):
    if not client:
        return {"error": "OpenAI client not initialized."}

    body = await request.json()
    message = body.get("message", "")
    if not message:
        return {"error": "Empty message."}

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": message}]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
