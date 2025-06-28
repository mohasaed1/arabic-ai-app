# main.py
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
            return {"reply": "❌ البيانات غير كافية للإجابة." if payload.lang == 'ar' else "❌ Not enough data to answer."}

        cols = data.columns.tolist()
        reply = ""

        if any(x in msg for x in ["average", "mean", "متوسط"]):
            numeric_cols = data.select_dtypes(include='number').columns.tolist()
            if numeric_cols:
                avg = data[numeric_cols].mean().round(2)
                reply = "\n".join([f"📊 {col}: {val}" for col, val in avg.items()])
            else:
                reply = "❌ لا توجد أعمدة رقمية لحساب المتوسط." if payload.lang == 'ar' else "❌ No numeric columns to average."

        elif any(x in msg for x in ["column", "العمود", "chart", "الرسم"]):
            reply = f"🧭 {'استخدم الرسم العمودي لعرض البيانات من العمود' if payload.lang == 'ar' else 'Use bar chart for column'}: {cols[0]}"

        elif any(x in msg for x in ["top", "الأكثر"]):
            top_stats = []
            for col in cols:
                if data[col].dtype == object:
                    freq = data[col].value_counts().head(3)
                    summary = ", ".join([f"{k} ({v})" for k, v in freq.items()])
                    top_stats.append(f"🗂️ {col}: {summary}")
            reply = "\n".join(top_stats) or ("❌ لا توجد أعمدة نصية." if payload.lang == 'ar' else "❌ No text columns found.")

        else:
            reply = "🔍 يمكنك طلب متوسط، رسم بياني، أو القيم المتكررة." if payload.lang == 'ar' else "🔍 You can ask for averages, charts, or top values."

        return {"reply": reply}

    except Exception as e:
        return {"reply": f"❌ خطأ في المعالجة: {str(e)}" if payload.lang == 'ar' else f"❌ Processing error: {str(e)}"}

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

        insights = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                insights[col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "avg": float(df[col].mean())
                }
            else:
                freq = df[col].value_counts().head(3).to_dict()
                insights[col] = {"top": freq}

        return {
            "headers": list(df.columns),
            "data": preview,
            "summary": summary,
            "insights": insights,
        }
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
