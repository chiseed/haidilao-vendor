# main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
import pandas as pd
import os
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        # 讀入為 DataFrame
        df_raw = pd.read_excel(file.file, header=None)
        target_headers = ["公司行號", "優惠折扣", "使用規則"]

        header_row_index = -1
        for i, row in df_raw.iterrows():
            if all(item in row.values.tolist() for item in target_headers):
                header_row_index = i
                break

        if header_row_index == -1:
            return JSONResponse(status_code=400, content={"message": "❌ Excel 檔案中找不到標題列（需包含：公司行號、優惠折扣、使用規則）"})

        # 重新讀入，指定 header 行
        file.file.seek(0)  # 重新定位檔案指標
        df = pd.read_excel(file.file, header=header_row_index)

        vendors = df[target_headers].dropna(subset=["公司行號"]).to_dict(orient="records")

        with open(VENDORS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(vendors, f, ensure_ascii=False, indent=2)

        return {"message": f"✅ 上傳成功，共 {len(vendors)} 筆資料"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"❌ 上傳失敗: {str(e)}"})

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
