from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import json
import os

app = FastAPI()

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VENDOR_JSON_PATH = "vendors.json"

@app.get("/vendors")
def get_vendors():
    if not os.path.exists(VENDOR_JSON_PATH):
        return JSONResponse(status_code=404, content={"message": "尚未上傳資料"})
    with open(VENDOR_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"data": data}

@app.post("/upload")
def upload_excel(file: UploadFile = File(...)):
    try:
        df = pd.read_excel(file.file)

        # 自動尋找包含必要欄位的起始列
        for i, row in df.iterrows():
            if {"公司行號", "優惠折扣", "使用規則"}.issubset(row.values):
                df.columns = df.iloc[i]
                df = df[i + 1:].reset_index(drop=True)
                break

        if not all(col in df.columns for col in ["公司行號", "優惠折扣", "使用規則"]):
            return JSONResponse(status_code=400, content={"message": f"接收到的欄位：{list(df.columns)}\n缺少必要欄位"})

        vendors = df[["公司行號", "優惠折扣", "使用規則"]].dropna(subset=["公司行號"]).to_dict(orient="records")
        with open(VENDOR_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(vendors, f, ensure_ascii=False, indent=2)

        return {"message": f"上傳成功，共 {len(vendors)} 筆"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"處理失敗：{str(e)}"})

# 首頁 index.html 回傳
@app.get("/", response_class=HTMLResponse)
def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# 靜態檔案 (圖片)
app.mount("/images", StaticFiles(directory="images"), name="images")
# 其他靜態資源（如 index.html 內需引用的 css, js）
app.mount("/static", StaticFiles(directory="."), name="static")
