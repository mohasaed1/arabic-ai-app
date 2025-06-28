# main.py (fixed version with date handling and better chat logic)
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uvicorn
import io
from typing import List, Optional, Dict

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
    keys: Optional[List[Dict[str, str]]] = None

class DetectKeysRequest(BaseModel):
    files: List[dict]

@app.post("/detect-keys")
def detect_keys(req: DetectKeysRequest):
    try:
        matches = []
        dfs = [(f['fileName'], pd.DataFrame(f['data'])) for f in req.files if 'data' in f]
        for i in range(len(dfs)):
            for j in range(i + 1, len(dfs)):
                name1, df1 = dfs[i]
                name2, df2 = dfs[j]
                for col1 in df1.columns:
                    for col2 in df2.columns:
                        overlap = len(set(df1[col1]) & set(df2[col2]))
                        if overlap > 0:
                            matches.append({
                                "file1": name1,
                                "col1": col1,
                                "file2": name2,
                                "col2": col2,
                                "score": overlap
                            })
        matches.sort(key=lambda x: -x['score'])
        return {"matches": matches[:10]}
    except Exception as e:
        return {"error": f"Key detection failed: {str(e)}"}

@app.post("/join-files")
def join_files(payload: JoinRequest):
    try:
        files = payload.files
        keys = payload.keys or []
        if len(files) < 2:
            return {"error": "Need at least 2 datasets to join."}

        names = [f"file{i}" for i in range(len(files))]
        dfs = {names[i]: pd.DataFrame(files[i]) for i in range(len(files))}

        joined = list(dfs.items())[0][1].copy()
        joins = []
        used = set([list(dfs.keys())[0]])
        for join in keys:
            f1, c1 = join['file1'], join['col1']
            f2, c2 = join['file2'], join['col2']
            if f1 in dfs and f2 in dfs:
                if f1 in used:
                    joined = pd.merge(joined, dfs[f2], left_on=c1, right_on=c2, how='left')
                    used.add(f2)
                    joins.append(f"Joined {f1}.{c1} = {f2}.{c2}")
                elif f2 in used:
                    joined = pd.merge(joined, dfs[f1], left_on=c2, right_on=c1, how='left')
                    used.add(f1)
                    joins.append(f"Joined {f2}.{c2} = {f1}.{c1}")

        preview = joined.head(5).to_dict(orient="records")
        return {"data": preview, "join_summary": joins or ["✅ Manual join completed"]}
    except Exception as e:
        return {"error": f"Join failed: {str(e)}"}

@app.post("/chat")
def chat_endpoint(payload: ChatRequest):
    try:
        df = pd.DataFrame(payload.data)
        msg = payload.message.lower()
        lang = payload.lang or 'en'
        if df.empty:
            return {"reply": "❌ البيانات غير كافية للإجابة." if lang == 'ar' else "❌ Not enough data to answer."}

        col_map = {
            'units': ['units', 'units sold', 'الوحدات'],
            'group': ['category', 'type', 'item', 'region', 'country', 'القسم', 'النوع']
        }

        metric_col = next((c for c in df.columns if any(k in c.lower() for k in col_map['units'])), None)
        group_col = next((c for c in df.columns if any(k in c.lower() for k in col_map['group'])), None)

        if metric_col:
            try:
                df[metric_col] = pd.to_numeric(df[metric_col], errors='coerce')
                df.dropna(subset=[metric_col], inplace=True)
            except:
                return {"reply": "❌ Unable to interpret metric column."}

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
        return {"reply": f"❌ خطأ في المعالجة: {str(e)}" if lang == 'ar' else f"❌ Processing error: {str(e)}"}

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
        summary = {"rows": len(df), "columns": list(df.columns)}

        insights = {}
        for col in df.columns:
            try:
                parsed = pd.to_datetime(df[col])
                if not parsed.isnull().all():
                    insights[col] = {
                        "type": "date",
                        "earliest": str(parsed.min().date()),
                        "latest": str(parsed.max().date())
                    }
                    continue
            except:
                pass

            if pd.api.types.is_numeric_dtype(df[col]) and 'id' not in col.lower():
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
            "insights": insights
        }
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
