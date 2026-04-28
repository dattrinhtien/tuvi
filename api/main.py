import unicodedata
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini (Updated with new Key)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

from lasotuvi.App import lapDiaBan
from lasotuvi.DiaBan import diaBan
from lasotuvi.ThienBan import lapThienBan

app = FastAPI(title="La So Tu Vi API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def remove_accents(input_str: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    res = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return res.replace('đ', 'd').replace('Đ', 'D')

class TuViInput(BaseModel):
    name: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: int
    gender: str
    calendar_type: str = "solar" # "solar" or "lunar"
    
    @field_validator('birth_hour')
    @classmethod
    def validate_birth_hour(cls, v):
        if not (1 <= v <= 12):
            raise ValueError('must be between 1 and 12 (1=Tý, ..., 12=Hợi)')
        return v
        
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        v_lower = v.lower()
        if v_lower not in ['nam', 'nu', 'nữ', 'male', 'female']:
            raise ValueError('must be nam/nu/male/female')
        return v_lower

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": ", ".join(errors)}
    )

@app.post("/tuvi")
def get_tuvi(data: TuViInput):
    try:
        gioi_tinh_int = 1 if data.gender.lower() in ['nam', 'male'] else -1
        is_solar_bool = True if data.calendar_type == "solar" else False
        
        db = lapDiaBan(
            diaBan, 
            nn=data.birth_day, 
            tt=data.birth_month, 
            nnnn=data.birth_year, 
            gioSinh=data.birth_hour, 
            gioiTinh=gioi_tinh_int, 
            duongLich=is_solar_bool, 
            timeZone=7
        )
        
        tb = lapThienBan(
            data.birth_day, 
            data.birth_month, 
            data.birth_year, 
            data.birth_hour, 
            gioi_tinh_int, 
            data.name, 
            db,
            duongLich=is_solar_bool
        )
        
        cung_dict = {}
        for i in range(1, 13):
            cung = db.thapNhiCung[i]
            cung_sao = []
            for sao in cung.cungSao:
                sao_name = sao['saoTen'] if isinstance(sao, dict) else sao.saoTen
                # Lấy thêm đắc tính nếu có
                dac_tinh = sao.get('saoDacTinh', '') if isinstance(sao, dict) else getattr(sao, 'saoDacTinh', '')
                if dac_tinh:
                    sao_name += f" ({dac_tinh})"
                cung_sao.append(sao_name)
            
            key = str(i)
            cung_dict[key] = {
                "name": cung.cungTen,
                "stars": cung_sao,
                "chu_cung": cung.cungChu,
                "dai_han": cung.cungDaiHan
            }

        result = {
            "success": True,
            "data": {
                "thien_ban": {
                    "ten": tb.ten,
                    "ngay_sinh": f"{data.birth_day}/{data.birth_month}/{data.birth_year}",
                    "nam_duong": tb.namDuong,
                    "thang_duong": tb.thangDuong,
                    "ngay_duong": tb.ngayDuong,
                    "gio_sinh": data.birth_hour,
                    "gioi_tinh": data.gender,
                    "am_duong_nam_nu": f"{tb.amDuongNamSinh} {tb.namNu}",
                    "menh": tb.menh,
                    "cuc": tb.tenCuc,
                    "ban_menh": tb.banMenh,
                    "nam_am": f"{tb.canNamTen} {tb.chiNamTen}",
                    "thang_am": f"{tb.canThangTen} {tb.chiThangTen}",
                    "ngay_am": f"{tb.canNgayTen} {tb.chiNgayTen}",
                    "gio_am": tb.gioSinh,
                    "menh_chu": tb.menhChu,
                    "than_chu": tb.thanChu,
                    "sinh_khac": tb.sinhKhac
                },
                "cung": cung_dict,
                "interpretation": "" # Placeholder
            }
        }
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

class InterpretInput(BaseModel):
    data: dict

@app.post("/interpret")
async def interpret_tuvi(input_data: InterpretInput):
    try:
        data = input_data.data
        thien_ban = data.get("thien_ban", {})
        cung_dict = data.get("cung", {})
        
        # Xây dựng Prompt
        cung_info = "\n".join([f"Cung {v['chu_cung']} ({v['name']}): {', '.join(v['stars'])}" for k, v in cung_dict.items()])
        
        prompt_text = f"""
        Bạn là Đại đệ tử của sư phụ Trịnh Tiến Đạt, một chuyên gia bậc thầy về Tử Vi Lý Số với hơn 30 năm kinh nghiệm. 
        **Bối cảnh thời gian:** Hôm nay là tháng 4 năm 2026 (năm Bính Ngọ). Hãy dùng mốc này để tính toán các tiểu hạn.

        Hãy dùng phong thái của một đại sư để luận giải lá số Tử Vi cho người có thông tin sau:
        - Họ tên: {thien_ban.get('ten')}
        - Năm sinh: {thien_ban.get('nam_am')} ({thien_ban.get('nam_duong')})
        - Bản mệnh: {thien_ban.get('ban_menh')}, Cục: {thien_ban.get('cuc')}
        - Chủ mệnh: {thien_ban.get('menh_chu')}, Chủ thân: {thien_ban.get('than_chu')}
        - Tương quan: {thien_ban.get('sinh_khac')}

        Chi tiết các cung và sao:
        {cung_info}

        Hãy trình bày bài luận giải theo các phần sau:
        1. Lời chào và Tổng quan: Giới thiệu mình là Đại đệ tử của sư phụ Trịnh Tiến Đạt. Nhận định khái quát về lá số.
        2. Bản mệnh và Tính cách: Phân tích sâu về tư duy, ưu nhược điểm của đương số.
        3. Sự nghiệp và Tài lộc: Các cột mốc quan trọng và hướng phát triển.
        4. Tình duyên và Gia đạo: Các mối quan hệ và hạnh phúc lứa đôi.
        5. Phân tích Đại hạn hiện tại: Vận trình 10 năm hiện tại (đại hạn bao nhiêu tuổi) thăng trầm ra sao?
        6. Phân tích 3 năm liên tiếp (Tiểu hạn):
           - Năm ngoái (2025 - Ất Tỵ): Những sự kiện nổi bật đã qua.
           - Năm nay (2026 - Bính Ngọ): Cơ hội, thách thức và những việc nên làm.
           - Năm sang năm (2027 - Đinh Mùi): Dự báo và chuẩn bị.
        7. Phân tích thăng trầm cuộc đời qua các Đại hạn: Không dùng bảng, hãy viết thành các đoạn văn phân tích mạch lạc về dòng chảy vận mệnh qua từng giai đoạn 10 năm của đương số (từ trẻ đến già).
        8. Lời khuyên cuối cùng và hướng phát triển bản thân.

        Yêu cầu: Ngôn ngữ uyên bác, thâm thúy, định dạng Markdown chuyên nghiệp.
        """

        # Danh sách các model để thử (phòng trường hợp quá tải)
        models_to_try = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-flash-latest'
        ]
        
        last_error = ""
        import requests
        import json

        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt_text}]
                    }]
                }

                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
                resp_json = response.json()
                
                if response.status_code == 200:
                    interpretation = resp_json['candidates'][0]['content']['parts'][0]['text']
                    return {"success": True, "interpretation": interpretation}
                else:
                    # Nếu lỗi do quá tải (503, 429 hoặc message chứa high demand), thử model tiếp theo
                    error_msg = resp_json.get('error', {}).get('message', 'Lỗi không xác định')
                    last_error = error_msg
                    if "high demand" in error_msg.lower() or response.status_code in [429, 503]:
                        continue
                    else:
                        break # Nếu là lỗi khác (như sai Key) thì dừng lại luôn
            except Exception as e:
                last_error = str(e)
                continue
                
        return {"success": False, "error": f"Tất cả các model AI đều đang bận hoặc gặp lỗi: {last_error}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
