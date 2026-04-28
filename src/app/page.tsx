'use client';

import { useState } from 'react';

const HOUR_OPTIONS = [
  { value: 1, label: 'Tý (23h-01h)' },
  { value: 2, label: 'Sửu (01h-03h)' },
  { value: 3, label: 'Dần (03h-05h)' },
  { value: 4, label: 'Mão (05h-07h)' },
  { value: 5, label: 'Thìn (07h-09h)' },
  { value: 6, label: 'Tỵ (09h-11h)' },
  { value: 7, label: 'Ngọ (11h-13h)' },
  { value: 8, label: 'Mùi (13h-15h)' },
  { value: 9, label: 'Thân (15h-17h)' },
  { value: 10, label: 'Dậu (17h-19h)' },
  { value: 11, label: 'Tuất (19h-21h)' },
  { value: 12, label: 'Hợi (21h-23h)' },
];

const GRID_MAP = [
  6, 7, 8, 9,
  5, 'center', 'center', 10,
  4, 'center', 'center', 11,
  3, 2, 1, 12
];

const MAIN_STARS = ['tử vi', 'liêm trinh', 'thiên đồng', 'vũ khúc', 'thái dương', 'thiên cơ', 'thiên phủ', 'thái âm', 'tham lang', 'cự môn', 'thiên tướng', 'thiên lương', 'thất sát', 'phá quân'];
const GOOD_STARS = ['hóa lộc', 'hóa quyền', 'hóa khoa', 'lộc tồn', 'thiên khôi', 'thiên việt', 'tả phụ', 'hữu bật', 'văn xương', 'văn khúc', 'đào hoa', 'hồng loan', 'hỷ thần', 'đường phù', 'giải thần', 'phượng các', 'long trì', 'thiên mã', 'thiên hỷ', 'thiên quý', 'ân quang', 'tam thai', 'bát tọa', 'phong cáo', 'thai phụ', 'quốc ấn', 'tấu thư', 'hoa cái', 'thiên phúc', 'thiên quan', 'nguyệt đức', 'phúc đức', 'thiên đức', 'thiên giải', 'địa giải', 'thiên y', 'thiên trù', 'thanh long', 'lưu hà', 'thiên tài', 'thiên thọ', 'tràng sinh', 'đế vượng', 'mộc dục', 'quan đới', 'lâm quan', 'dưỡng', 'thai', 'bác sỹ', 'lực sĩ', 'tướng quân'];
const BAD_STARS = ['địa không', 'địa kiếp', 'kình dương', 'đà la', 'hỏa tinh', 'linh tinh', 'hóa kỵ', 'thiên hình', 'thiên khốc', 'thiên hư', 'đại hao', 'tiểu hao', 'tang môn', 'bạch hổ', 'điếu khách', 'tuế phá', 'cô thần', 'quả tú', 'phục binh', 'kiếp sát', 'thiên sứ', 'thiên thương', 'lưu hà', 'phá toái', 'đẩu quân', 'suy', 'bệnh', 'tử', 'mộ', 'tuyệt', 'bệnh phù', 'quan phù'];

export default function Home() {
  const [formData, setFormData] = useState({
    name: 'Nguyễn Văn A',
    birth_year: 1982,
    birth_month: 10,
    birth_day: 7,
    birth_hour: 6,
    gender: 'nam',
    calendar_type: 'solar',
  });

  const [result, setResult] = useState<any>(null);
  const [interpretation, setInterpretation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['birth_year', 'birth_month', 'birth_day', 'birth_hour'].includes(name) 
        ? parseInt(value) || 0 
        : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setInterpretation(null);

    try {
      const response = await fetch('/api/tuvi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      if (data.success) {
        setResult(data.data);
      } else {
        throw new Error(data.error || 'Có lỗi xảy ra');
      }
    } catch (err: any) {
      setError(err.message || 'Có lỗi kết nối tới server');
    } finally {
      setLoading(false);
    }
  };

  const handleInterpret = async () => {
    if (!result) return;
    setAiLoading(true);
    setInterpretation(null);
    try {
      const response = await fetch('/api/interpret', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: result }),
      });
      const data = await response.json();
      if (data.success) {
        setInterpretation(data.interpretation);
      } else {
        throw new Error(data.error || 'Lỗi gọi AI');
      }
    } catch (err: any) {
      setInterpretation(`Lỗi: ${err.message}`);
    } finally {
      setAiLoading(false);
    }
  };

  const renderStars = (stars: string[]) => {
    const main: string[] = [];
    const good: string[] = [];
    const bad: string[] = [];

    stars.forEach(s => {
      const ls = s.toLowerCase();
      if (MAIN_STARS.some(m => ls.includes(m))) main.push(s);
      else if (GOOD_STARS.some(g => ls.includes(g))) good.push(s);
      else if (BAD_STARS.some(b => ls.includes(b))) bad.push(s);
      else good.push(s);
    });

    return (
      <div className="flex w-full h-full text-[10px] leading-tight mt-1">
        <div className="w-[35%] flex flex-col items-start gap-1 text-red-600 font-medium overflow-hidden">
          {good.map((s, i) => <span key={i} className="whitespace-nowrap">{s}</span>)}
        </div>
        <div className="w-[30%] flex flex-col items-center gap-1 font-bold text-[#8b0000] px-1 text-center uppercase border-l border-r border-gray-100">
          {main.map((s, i) => <span key={i} className="text-[12px] leading-tight mb-2">{s}</span>)}
        </div>
        <div className="w-[35%] flex flex-col items-end gap-1 text-gray-500 overflow-hidden text-right">
          {bad.map((s, i) => <span key={i} className="whitespace-nowrap">{s}</span>)}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#e8e4d9] text-[#222] p-2 md:p-6 font-sans">
      <main className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-6">
        
        {/* Sidebar */}
        <div className="lg:w-80 flex-shrink-0">
          <div className="bg-white p-5 rounded shadow-sm border border-gray-300">
            <h1 className="text-xl font-bold text-[#8b0000] border-b-2 border-[#8b0000] mb-4 pb-1 uppercase italic">Tử Vi Số Mệnh</h1>
            <form onSubmit={handleSubmit} className="space-y-3">
              <input className="w-full border border-gray-300 p-2 text-sm rounded outline-none" type="text" name="name" value={formData.name} onChange={handleChange} placeholder="Họ tên" />
              <div className="grid grid-cols-2 gap-2">
                <select className="border border-gray-300 p-2 text-sm rounded bg-white" name="calendar_type" value={formData.calendar_type} onChange={handleChange}>
                  <option value="solar">Dương Lịch</option>
                  <option value="lunar">Âm Lịch</option>
                </select>
                <select className="border border-gray-300 p-2 text-sm rounded bg-white" name="gender" value={formData.gender} onChange={handleChange}>
                  <option value="nam">Nam</option>
                  <option value="nu">Nữ</option>
                </select>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <input className="border border-gray-300 p-2 text-sm rounded" type="number" name="birth_day" value={formData.birth_day} onChange={handleChange} />
                <input className="border border-gray-300 p-2 text-sm rounded" type="number" name="birth_month" value={formData.birth_month} onChange={handleChange} />
                <input className="border border-gray-300 p-2 text-sm rounded" type="number" name="birth_year" value={formData.birth_year} onChange={handleChange} />
              </div>
              <select className="w-full border border-gray-300 p-2 text-sm rounded bg-white" name="birth_hour" value={formData.birth_hour} onChange={handleChange}>
                {HOUR_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
              </select>
              <button type="submit" disabled={loading} className="w-full bg-[#8b0000] text-white py-2 font-bold uppercase hover:bg-black transition-colors shadow-sm disabled:bg-gray-400">
                {loading ? 'Đang an sao...' : 'Lập Lá Số'}
              </button>
            </form>
            {error && <div className="mt-3 p-2 bg-red-50 text-red-600 text-xs border border-red-200">{error}</div>}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto space-y-8 pb-20">
          {!result ? (
            <div className="bg-white/50 h-96 rounded border-2 border-dashed border-gray-400 flex items-center justify-center text-gray-400 italic font-serif text-xl">Vui lòng nhập thông tin để xem lá số</div>
          ) : (
            <>
              <div className="inline-block bg-[#333] p-[1px] shadow-2xl">
                <div className="grid grid-cols-4 grid-rows-4 w-[900px] h-[900px] bg-[#333] gap-[1px]">
                  {GRID_MAP.map((pos, index) => {
                    if (pos === 'center') {
                      if (index === 5) {
                        return (
                          <div key="center-tb" className="col-span-2 row-span-2 bg-white flex flex-col p-8 relative overflow-hidden">
                            <div className="absolute inset-0 opacity-5 pointer-events-none flex items-center justify-center">
                              <div className="w-64 h-64 border-8 border-[#8b0000] rounded-full flex items-center justify-center"><span className="text-8xl font-serif font-bold text-[#8b0000]">TỬ VI</span></div>
                            </div>
                            <div className="relative z-10 w-full text-center">
                              <h2 className="text-3xl font-serif font-bold text-[#8b0000] mb-6">Lá Số Tử Vi</h2>
                              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-left text-[13px] border-y py-4 border-gray-100">
                                <p><span className="font-bold w-20 inline-block">Họ tên:</span> {result.thien_ban.ten}</p>
                                <p><span className="font-bold w-20 inline-block">Giới tính:</span> {result.thien_ban.gioi_tinh === 'nam' ? 'Nam' : 'Nữ'}</p>
                                <p><span className="font-bold w-20 inline-block">Năm:</span> {result.thien_ban.nam_am} ({result.thien_ban.nam_duong})</p>
                                <p><span className="font-bold w-20 inline-block">Dương lịch:</span> {result.thien_ban.ngay_sinh}</p>
                                <p><span className="font-bold w-20 inline-block">Tháng:</span> {result.thien_ban.thang_am}</p>
                                <p><span className="font-bold w-20 inline-block">Giờ sinh:</span> {result.thien_ban.gio_am}</p>
                                <p><span className="font-bold w-20 inline-block">Ngày:</span> {result.thien_ban.ngay_am}</p>
                                <p><span className="font-bold w-20 inline-block">Âm dương:</span> {result.thien_ban.am_duong_nam_nu}</p>
                                <p><span className="font-bold w-20 inline-block">Bản mệnh:</span> {result.thien_ban.ban_menh}</p>
                                <p><span className="font-bold w-20 inline-block">Cục:</span> {result.thien_ban.cuc}</p>
                                <p><span className="font-bold w-20 inline-block">Chủ mệnh:</span> {result.thien_ban.menh_chu}</p>
                                <p><span className="font-bold w-20 inline-block">Chủ thân:</span> {result.thien_ban.than_chu}</p>
                              </div>
                              <div className="mt-6 font-bold text-[#8b0000] bg-red-50 p-2 border border-red-100 uppercase">{result.thien_ban.sinh_khac}</div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }
                    const cungData = result.cung[pos.toString()];
                    const isMenh = cungData.chu_cung === 'Mệnh';
                    return (
                      <div key={pos} className="bg-white p-2 flex flex-col relative border border-gray-100">
                        <div className="flex justify-between items-center border-b border-gray-100 pb-1 mb-1">
                          <span className="text-[11px] font-bold text-gray-500">{cungData.name}</span>
                          <span className={`text-[13px] font-black uppercase ${isMenh ? 'text-white bg-[#8b0000] px-2 py-0.5 rounded' : 'text-[#8b0000]'}`}>{cungData.chu_cung}</span>
                          <span className="text-[11px] font-bold text-gray-500">{cungData.dai_han}</span>
                        </div>
                        <div className="flex-1 overflow-hidden">{renderStars(cungData.stars)}</div>
                        <div className="mt-auto pt-1 flex justify-between text-[9px] font-bold text-gray-400 border-t border-gray-50">
                          <span>ĐV.{cungData.chu_cung}</span>
                          <span>{cungData.stars.find((s:string) => ['tràng sinh', 'mộc dục', 'quan đới', 'lâm quan', 'đế vượng', 'suy', 'bệnh', 'tử', 'mộ', 'tuyệt', 'thai', 'dưỡng'].some(t => s.toLowerCase().includes(t))) || ''}</span>
                          <span>LN.{cungData.chu_cung}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Phần luận giải AI */}
              <div className="max-w-[900px] flex flex-col items-center">
                {!interpretation && !aiLoading && (
                  <button 
                    onClick={handleInterpret}
                    className="bg-[#8b0000] text-white px-10 py-4 rounded-full font-bold text-xl shadow-lg hover:bg-black transition-all transform hover:scale-105"
                  >
                    ✨ XEM LUẬN GIẢI AI CHI TIẾT ✨
                  </button>
                )}

                {(aiLoading || interpretation) && (
                  <div className="bg-white p-8 rounded-lg shadow-xl border border-gray-200 w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center gap-3 mb-6 border-b-2 border-[#8b0000] pb-2">
                      <div className="w-10 h-10 bg-[#8b0000] rounded-full flex items-center justify-center shadow-lg text-white font-bold">AI</div>
                      <h3 className="text-2xl font-serif font-bold text-[#8b0000]">Luận Giải Từ Đại Sư AI</h3>
                    </div>
                    
                    {aiLoading ? (
                      <div className="flex flex-col items-center py-20 text-gray-400 italic">
                        <div className="w-12 h-12 border-4 border-[#8b0000] border-t-transparent rounded-full animate-spin mb-4"></div>
                        <p className="text-lg">Đại sư AI đang chiêm nghiệm lá số...</p>
                        <p className="text-sm mt-2">Quá trình này có thể mất 15-30 giây.</p>
                      </div>
                    ) : (
                      <div className="max-w-none text-gray-800 leading-relaxed whitespace-pre-wrap font-serif text-lg space-y-4">
                        {interpretation}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
