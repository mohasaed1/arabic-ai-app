# main.py (FastAPI backend)
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uvicorn
import io
import json
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    data: List[dict]
    lang: Optional[str] = "en"

@app.post("/chat")
def chat_endpoint(payload: ChatRequest):
    try:
        msg = payload.message.lower()
        data = pd.DataFrame(payload.data)
        if data.empty:
            return {"reply": "❌ البيانات غير كافية للإجابة."}

        cols = data.columns.tolist()
        reply = ""

        if any(x in msg for x in ["average", "mean", "متوسط"]):
            numeric_cols = data.select_dtypes(include='number').columns.tolist()
            if numeric_cols:
                avg = data[numeric_cols].mean().round(2)
                reply = "\n".join([f"📊 {col}: {val}" for col, val in avg.items()])
            else:
                reply = "❌ لا توجد أعمدة رقمية لحساب المتوسط."
        elif any(x in msg for x in ["column", "الرسم", "chart"]):
            reply = f"🧭 استخدم الرسم العمودي لعرض البيانات من العمود: {cols[0]}"
        else:
            reply = "🔍 تم تحليل الملف بنجاح. يمكنك طلب ملخص، رسم، أو إحصاء."

        return {"reply": reply}
    except Exception as e:
        return {"reply": f"❌ خطأ في المعالجة: {str(e)}"}

@app.post("/upload-file")
def upload_file(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        elif file.filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {"error": "Unsupported file format."}

        preview = df.head(5).to_dict(orient="records")
        summary = {
            "rows": len(df),
            "columns": list(df.columns),
        }

        return {
            "headers": list(df.columns),
            "data": preview,
            "summary": summary,
        }
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
