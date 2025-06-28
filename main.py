# main.py (joins multiple uploaded tables with key inference)
from fastapi import FastAPI, File, UploadFile
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

class JoinRequest(BaseModel):
    files: List[List[dict]]

# Helper to infer join keys between dataframes
def infer_joins(dfs):
    merged = dfs[0].copy()
    join_info = []
    for i in range(1, len(dfs)):
        df2 = dfs[i]
        best_match = None
        best_score = 0
        for col1 in merged.columns:
            for col2 in df2.columns:
                common = len(set(merged[col1]) & set(df2[col2]))
                if common > best_score:
                    best_score = common
                    best_match = (col1, col2)
        if best_match and best_score > 0:
            merged = pd.merge(merged, df2, left_on=best_match[0], right_on=best_match[1], how='left')
            join_info.append(f"Joined on {best_match[0]} = {best_match[1]}")
    return merged, join_info

@app.post("/chat")
def chat_endpoint(payload: ChatRequest):
    try:
        df = pd.DataFrame(payload.data)
        msg = payload.message.lower()
        lang = payload.lang or 'en'
        if df.empty:
            return {"reply": "❌ البيانات غير كافية للإجابة." if lang == 'ar' else "❌ Not enough data to answer."}

        targets = ['total', 'sum', 'average', 'count', 'اجمالي', 'مجموع', 'متوسط', 'عدد']
        metric_col = next((col for col in df.columns if any(k in col.lower() for k in ['revenue', 'profit', 'cost', 'sold', 'price', 'units', 'مبيعات', 'الربح'])), None)
        group_col = next((col for col in df.columns if any(k in col.lower() for k in ['category', 'type', 'item', 'region', 'country', 'القسم', 'النوع'])), None)

        if any(t in msg for t in targets) and metric_col:
            if group_col and group_col != metric_col:
                summary = df.groupby(group_col)[metric_col].sum().sort_values(ascending=False).head(5)
                lines = [f"📊 {k}: {v:.2f}" for k, v in summary.items()]
                reply = "\n".join(lines)
            else:
                total = df[metric_col].sum()
                reply = f"📊 {metric_col}: {total:.2f}"
        else:
            reply = "🔍 يمكنك طرح أي سؤال حول المبيعات أو الأداء، وسنقوم بالتحليل." if lang == 'ar' else "🔍 Ask any question about sales or performance, and we'll analyze it."

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

@app.post("/join-files")
def join_files(payload: JoinRequest):
    try:
        dfs = [pd.DataFrame(f) for f in payload.files if isinstance(f, list) and len(f) > 0]
        if len(dfs) < 2:
            return {"error": "Need at least 2 datasets to join."}

        merged, join_info = infer_joins(dfs)
        preview = merged.head(5).to_dict(orient="records")

        return {
            "data": preview,
            "join_summary": join_info
        }
    except Exception as e:
        return {"error": f"Join failed: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
