import unicodedata
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
import requests
import json
import traceback

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Thiết lập đường dẫn cho Vercel
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# Import engine
try:
    from lasotuvi.App import lapDiaBan
    from lasotuvi.DiaBan import diaBan
    from lasotuvi.ThienBan import lapThienBan
except Exception as e:
    INIT_ERROR = f"Lỗi Import Engine: {str(e)}"
else:
    INIT_ERROR = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TuViInput(BaseModel):
    name: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: int
    gender: str
    calendar_type: str = "solar"

@app.post("/api")
async def get_tuvi(data: TuViInput):
    if INIT_ERROR: return {"success": False, "error": INIT_ERROR}
    try:
        gioi_tinh_int = 1 if data.gender.lower() in ['nam', 'male'] else -1
        is_solar_bool = True if data.calendar_type == "solar" else False
        db = lapDiaBan(diaBan, nn=data.birth_day, tt=data.birth_month, nnnn=data.birth_year, gioSinh=data.birth_hour, gioiTinh=gioi_tinh_int, duongLich=is_solar_bool, timeZone=7)
        tb = lapThienBan(data.birth_day, data.birth_month, data.birth_year, data.birth_hour, gioi_tinh_int, data.name, db, duongLich=is_solar_bool)
        
        cung_dict = {}
        for i in range(1, 13):
            cung = db.thapNhiCung[i]
            cung_sao = []
            for sao in cung.cungSao:
                sao_name = sao['saoTen'] if isinstance(sao, dict) else sao.saoTen
                dac_tinh = sao.get('saoDacTinh', '') if isinstance(sao, dict) else getattr(sao, 'saoDacTinh', '')
                if dac_tinh: sao_name += f" ({dac_tinh})"
                cung_sao.append(sao_name)
            cung_dict[str(i)] = {"name": cung.cungTen, "stars": cung_sao, "chu_cung": cung.cungChu, "dai_han": cung.cungDaiHan}

        return {
            "success": True,
            "data": {
                "thien_ban": {
                    "ten": tb.ten, "ngay_sinh": f"{data.birth_day}/{data.birth_month}/{data.birth_year}",
                    "nam_duong": tb.namDuong, "am_duong_nam_nu": f"{tb.amDuongNamSinh} {tb.namNu}",
                    "menh": tb.menh, "cuc": tb.tenCuc, "ban_menh": tb.banMenh,
                    "nam_am": f"{tb.canNamTen} {tb.chiNamTen}", "thang_am": f"{tb.canThangTen} {tb.chiThangTen}",
                    "ngay_am": f"{tb.canNgayTen} {tb.chiNgayTen}", "gio_am": tb.gioSinh,
                    "menh_chu": tb.menhChu, "than_chu": tb.thanChu if hasattr(tb, 'thanChu') else getattr(tb, 'than_chu', 'N/A'),
                    "sinh_khac": tb.sinhKhac
                },
                "cung": cung_dict
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Engine Crash: {str(e)}"}

@app.post("/api/interpret")
async def interpret_tuvi(input_data: dict):
    try:
        data = input_data.get("data", {})
        thien_ban = data.get("thien_ban", {})
        cung_dict = data.get("cung", {})
        cung_info = "\n".join([f"Cung {v['chu_cung']} ({v['name']}): {', '.join(v['stars'])}" for k, v in cung_dict.items()])
        prompt_text = f"Luận giải Tử Vi cho {thien_ban.get('ten')}. 2026. Data: {cung_info}"
        
        models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt_text}]}]}, timeout=60)
            if resp.status_code == 200:
                return {"success": True, "interpretation": resp.json()['candidates'][0]['content']['parts'][0]['text']}
        return {"success": False, "error": "AI bận"}
    except Exception as e:
        return {"success": False, "error": str(e)}
