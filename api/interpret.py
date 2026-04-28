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
        cung_info = "\n".join([f"Cung {v['chu_cung']} ({v['name']}): {', '.join(v['stars'])}" for k, v in cung_dict.items()])
        
        prompt_text = f"Luận giải Tử Vi cho {thien_ban.get('ten')}. Hôm nay là tháng 4/2026. Phân tích: Bản mệnh, Sự nghiệp, Tình duyên, Đại hạn hiện tại và Tiểu hạn 3 năm 2025-2027. Vẽ thăng trầm bằng các đoạn văn thâm thúy.\nChi tiết: {cung_info}"

        if not GEMINI_API_KEY:
            return {"success": False, "error": "Thiếu Gemini API Key trên Vercel"}

        models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                return {"success": True, "interpretation": response.json()['candidates'][0]['content']['parts'][0]['text']}
        
        return {"success": False, "error": f"AI đang bận: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
