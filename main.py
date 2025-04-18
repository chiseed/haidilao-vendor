# main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import pandas as pd
import json
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VENDORS_JSON_PATH = "vendors.json"

@app.get("/vendors")
def get_vendors():
    if not os.path.exists(VENDORS_JSON_PATH):
        return JSONResponse(status_code=404, content={"message": "尚未上傳任何資料"})
    with open(VENDORS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"data": data}

@app.post("/upload")
def upload_excel(file: UploadFile = File(...)):
    try:
        df = pd.read_excel(file.file)
        required_cols = ["公司行號", "優惠折扣", "使用規則"]
        if not all(col in df.columns for col in required_cols):
            return JSONResponse(status_code=400, content={"message": "Excel 檔案格式錯誤，缺少必要欄位"})

        vendors = df[required_cols].dropna(subset=["公司行號"]).to_dict(orient="records")

        with open(VENDORS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(vendors, f, ensure_ascii=False, indent=2)

        return {"message": "上傳成功，共有 {} 筆資料".format(len(vendors))}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"上傳失敗: {str(e)}"})
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()