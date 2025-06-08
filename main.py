from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS setup for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain later
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "🚀 Arabic AI API is running!"}

@app.post("/analyze")
async def analyze_text(request: Request):
    data = await request.json()
    text = data.get("text", "")

    # Placeholder logic – later we'll use HuggingFace / CAMeL
    return {
        "summary": "هذا ملخص تجريبي للنص.",
        "sentiment": "محايد",
        "keywords": ["ذكاء", "اصطناعي", "تحليل"]
    }
