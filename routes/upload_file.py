from fastapi import APIRouter, UploadFile, File
import pandas as pd
from io import BytesIO

router = APIRouter()

@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file into DataFrame
        contents = await file.read()
        extension = file.filename.split(".")[-1].lower()

        if extension in ["xlsx", "xls"]:
            df = pd.read_excel(BytesIO(contents))
        elif extension == "csv":
            df = pd.read_csv(BytesIO(contents))
        else:
            return {"error": f"Unsupported file format: .{extension}"}

        # Extract info
        preview = df.head(5).to_dict(orient="records")
        summary = df.describe(include="all").fillna("").to_dict()
        headers = list(df.columns)

        # Auto insights
        insights = {}
        for col in df.select_dtypes(include=["number"]).columns:
            insights[col] = {
                "sum": df[col].sum(),
                "mean": df[col].mean(),
                "max": df[col].max(),
                "min": df[col].min(),
                "median": df[col].median()
            }

        return {
            "headers": headers,
            "preview": preview,
            "summary": summary,
            "insights": insights,
            "rows": len(df)
        }

    except Exception as e:
        return {"error": f"File processing failed: {str(e)}"}
