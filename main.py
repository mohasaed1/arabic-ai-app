print("🚀 Arabic AI App is starting...")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
import requests
import os
from openai import OpenAI
client = None


app = FastAPI()

# ✅ Ensure global OpenAI key is declared at the top
OPENAI_API_KEY = None

# ✅ CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For prod: use ["https://app.gateofai.com"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Securely load OpenAI key from WordPress on startup

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
        OPENAI_API_KEY = response.json().get("key")
        if OPENAI_API_KEY:
            client = OpenAI(api_key=OPENAI_API_KEY)
            print("✅ OpenAI key loaded and client initialized.")
        else:
            print("⚠️ No key found in WP response.")
    except Exception as e:
        print("❌ Failed to fetch OpenAI key:", e)

# ✅ Basic test route
@app.get("/")
def home():
    return JSONResponse(content={"message": "🚀 Arabic AI API is running!"})

# ✅ Debug endpoint
@app.get("/debug-key")
def debug_key():
    global OPENAI_API_KEY
    return {"key_loaded": bool(OPENAI_API_KEY)}

# ✅ Analyzer dummy
@app.post("/analyze")
async def analyze_text(request: Request):
    data = await request.json()
    return JSONResponse(content={
        "summary": "هذا ملخص تجريبي للنص.",
        "sentiment": "محايد",
        "keywords": ["ذكاء", "اصطناعي", "تحليل"]
    })

# ✅ Analyzer w/ query
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
        avg = round(sum(ratios) / len(ratios), 2) if ratios else 0
        return {"answer": f"🔍 متوسط نسبة الربح إلى التكلفة هو {avg}"}
    return {"answer": "❌ لم أتمكن من فهم الاستعلام."}

# ✅ Chat route using OpenAI
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_gpt(req: ChatRequest):
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

# ✅ Local dev runner
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
