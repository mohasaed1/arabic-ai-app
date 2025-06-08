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
