import os
import sys
import json
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Thiết lập đường dẫn
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class InterpretInput(BaseModel):
    data: dict

@app.post("/api/interpret")
async def interpret_tuvi(input_data: InterpretInput):
    try:
        data = input_data.data
        thien_ban = data.get("thien_ban", {})
        cung_dict = data.get("cung", {})
        
        # Xây dựng thông tin các cung để gửi cho AI
        cung_info = "\n".join([f"Cung {v['chu_cung']} ({v['name']}): {', '.join(v['stars'])}" for k, v in cung_dict.items()])
        
        prompt_text = f"""
        Bạn là Đại đệ tử của sư phụ Trịnh Tiến Đạt, một chuyên gia bậc thầy về Tử Vi Lý Số với hơn 30 năm kinh nghiệm. 
        **Bối cảnh thời gian:** Hôm nay là tháng 4 năm 2026 (năm Bính Ngọ). Hãy dùng mốc này để tính toán các tiểu hạn cho chính xác.

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

        Yêu cầu quan trọng: 
        - Ngôn ngữ uyên bác, thâm thúy nhưng chân thành. 
        - Phải tính đúng tuổi đương số dựa trên mốc năm hiện tại là 2026.
        - Định dạng Markdown chuyên nghiệp (sử dụng các tiêu đề, in đậm để dễ đọc).
        """

        if not GEMINI_API_KEY:
            return {"success": False, "error": "Thiếu Gemini API Key trên Vercel. Hãy kiểm tra Environment Variables."}

        # Danh sách các model để thử (phòng trường hợp quá tải)
        models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']
        
        last_error = ""
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
                response = requests.post(url, json=payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    interpretation = result['candidates'][0]['content']['parts'][0]['text']
                    return {"success": True, "interpretation": interpretation}
                else:
                    error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                    last_error = error_msg
                    if "high demand" in error_msg.lower() or response.status_code in [429, 503]:
                        continue
                    else:
                        break
            except Exception as e:
                last_error = str(e)
                continue
        
        return {"success": False, "error": f"AI đang bận: {last_error}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
