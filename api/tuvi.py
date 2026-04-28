import os
import sys
import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# Thiết lập đường dẫn để import engine
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

try:
    from lasotuvi.App import lapDiaBan
    from lasotuvi.DiaBan import diaBan
    from lasotuvi.ThienBan import lapThienBan
except ImportError:
    # Dự phòng cho môi trường local
    sys.path.append(os.path.join(CURRENT_DIR, '..'))
    from api.lasotuvi.App import lapDiaBan
    from api.lasotuvi.DiaBan import diaBan
    from api.lasotuvi.ThienBan import lapThienBan

def handler(event, context):
    # Đây là hàm handler chuẩn cho Vercel Serverless (nếu không dùng FastAPI)
    # Tuy nhiên Vercel hỗ trợ FastAPI nếu chúng ta export app. 
    # Để an toàn nhất, tôi sẽ viết theo dạng function đơn giản.
    pass

# Nhưng để tận dụng Pydantic, tôi vẫn dùng FastAPI nhưng export app đúng cách
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class TuViInput(BaseModel):
    name: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: int
    gender: str
    calendar_type: str = "solar"

@app.post("/api/tuvi")
async def get_tuvi(data: TuViInput):
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
                    "nam_duong": tb.namDuong, "gioi_tinh": "nam" if gioi_tinh_int == 1 else "nu", "am_duong_nam_nu": f"{tb.amDuongNamSinh} {tb.namNu}",
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
        return {"success": False, "error": str(e)}
