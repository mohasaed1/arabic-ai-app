from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# CORS setup for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your frontend domain later
    allow_methods=["*"],
    allow_headers=["*"],
)

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
from pydantic import BaseModel
from typing import List, Dict

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

    return {"answer": "🤖 لم أتمكن من فهم الاستعلام أو حسابه من البيانات الحالية."}
