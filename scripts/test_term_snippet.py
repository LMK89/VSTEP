import asyncio
import os
import shutil
import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def get_ffmpeg_bin():
    if shutil.which("ffmpeg"):
        return "ffmpeg", "ffprobe"
    winget_path = r"C:\Users\khang.le\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
    return os.path.join(winget_path, "ffmpeg.exe"), os.path.join(winget_path, "ffprobe.exe")

FFMPEG_BIN, FFPROBE_BIN = get_ffmpeg_bin()

VOICE_VI = "vi-VN-NamMinhNeural"
VOICE_EN = "en-US-JennyNeural"

def get_audio_duration(file_path):
    cmd = [
        FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
        "-of", "json", file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    return float(data["format"]["duration"])

def make_silence(duration_sec, out_path):
    cmd = [
        FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec), "-c:a", "libmp3lame", "-b:a", "64k", out_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)

async def generate_chunk(text, voice, rate_str, out_path, max_retries=3):
    import edge_tts
    for attempt in range(max_retries):
        try:
            if rate_str:
                comm = edge_tts.Communicate(text, voice, rate=rate_str)
            else:
                comm = edge_tts.Communicate(text, voice)
            await comm.save(out_path)
            await asyncio.sleep(0.5)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error on chunk [{text[:30]}...]: {e}")
                raise e
            await asyncio.sleep(1.5)

# Snippet testing [vi], [term], and [en] integration
SNIPPET = [
    ("vi", "Hôm nay chúng ta cùng phân tích chuyên đề trọng tâm của Module 1: Bài một chấm hai, Quy tắc phối thì và xác định mốc thời gian. Trong bài thi học thuật VSTEP, các thì không đứng độc lập mà luôn vận hành trong một hệ thống liên kết chặt chẽ. Khái niệm này được gọi là"),
    ("term", "Tense Harmony"),
    ("vi", "tức là sự hài hòa về thì giữa các mệnh đề. Bây giờ chúng ta cùng nghe câu ví dụ kinh điển với liên từ"),
    ("term", "When"),
    ("en", "When penicillin was introduced during World War II, it proved to be a miracle drug that saved countless wounded soldiers."),
    ("vi", "Trong câu vừa rồi, hai động từ"),
    ("term", "was introduced"),
    ("vi", "và"),
    ("term", "proved"),
    ("vi", "đều chia ở quá khứ đơn. Và cụm từ"),
    ("term", "miracle drug"),
    ("vi", "chính là từ vựng B2 chỉ thần dược mang lại bước ngoặt điều trị.")
]

async def main():
    os.makedirs("output/temp_snippet", exist_ok=True)
    
    f_silence_05s = "output/temp_snippet/silence_05s.mp3"
    f_silence_10s = "output/temp_snippet/silence_10s.mp3"
    f_silence_15s = "output/temp_snippet/silence_15s.mp3"
    make_silence(0.5, f_silence_05s)
    make_silence(1.0, f_silence_10s)
    make_silence(1.5, f_silence_15s)
    
    parts = []
    print("[1/3] Đang sinh các audio chunks cho đoạn mẫu thử nghiệm [term]...")
    
    idx = 0
    for tag, text in SNIPPET:
        idx += 1
        print(f"  -> Xử lý chunk {idx}/{len(SNIPPET)} [{tag}]: {text[:35]}...")
        if tag == "vi":
            f_chunk = f"output/temp_snippet/chunk_{idx}_vi.mp3"
            await generate_chunk(text, VOICE_VI, None, f_chunk)
            parts.append(f_chunk)
        elif tag == "term":
            f_chunk = f"output/temp_snippet/chunk_{idx}_term.mp3"
            await generate_chunk(text, VOICE_EN, None, f_chunk)
            parts.append(f_chunk)
            parts.append(f_silence_05s) # 0.5s pause after term
        elif tag == "en":
            # EN Read 1 (0.9x) + 1.0s gap + EN Read 2 (1.0x) + 1.5s gap
            f_en1 = f"output/temp_snippet/chunk_{idx}_en_slow.mp3"
            f_en2 = f"output/temp_snippet/chunk_{idx}_en_normal.mp3"
            await generate_chunk(text, VOICE_EN, "-10%", f_en1)
            await generate_chunk(text, VOICE_EN, None, f_en2)
            parts.append(f_en1)
            parts.append(f_silence_10s)
            parts.append(f_en2)
            parts.append(f_silence_15s)

    # Concat
    concat_list = "output/temp_snippet/concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in parts:
            clean_p = os.path.abspath(p).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")
            
    out_sample = "output/sample_term_test.mp3"
    cmd_concat = [
        FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-ar", "24000", "-ac", "1", "-b:a", "64k", out_sample
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)
    dur = get_audio_duration(out_sample)
    
    print(f"\n[2/3] Sinh file mẫu thành công!")
    print(f"-> File: {os.path.abspath(out_sample)}")
    print(f"-> Thời lượng đoạn mẫu: {dur:.2f} giây ({int(dur//60)} phút {int(dur%60)} giây)")

    # Calculate exact duration for script-1-2-a.txt and script-1-2-b.txt
    print(f"\n[3/3] Tính toán lại thời lượng chính xác cho 2 tập:")
    for fname in ["podcast-scripts/script-1-2-a.txt", "podcast-scripts/script-1-2-b.txt"]:
        with open(fname, encoding="utf-8") as f:
            lines = f.read().split("\n")
        
        words_vi = 0
        num_terms = 0
        words_term = 0
        num_en = 0
        words_en = 0
        
        for l in lines:
            l = l.strip()
            if l.startswith("[vi] "):
                words_vi += len(l[5:].split())
            elif l.startswith("[term] "):
                num_terms += 1
                words_term += len(l[7:].split())
            elif l.startswith("[en] "):
                num_en += 1
                words_en += len(l[5:].split())
                
        # Time computation:
        # VI: 234 wpm
        t_vi = (words_vi / 234.0) * 60.0
        # Term: average ~0.8s speech + 0.5s pause = ~1.3s per term
        t_term = num_terms * 1.3
        # EN: read twice (0.9x + 1.0s + 1.0x + 1.5s) = ~18.6s per sentence
        t_en = num_en * 18.6
        
        total_sec = t_vi + t_term + t_en
        total_min = total_sec / 60.0
        
        print(f"\n--- {fname} ---")
        print(f"• Số từ tiếng Việt [vi]: {words_vi} từ ({t_vi/60:.1f} phút)")
        print(f"• Số thẻ thuật ngữ [term]: {num_terms} thẻ ({words_term} từ) ({t_term/60:.1f} phút)")
        print(f"• Số câu tiếng Anh [en]: {num_en} câu ({words_en} từ, đọc 2 lần) ({t_en/60:.1f} phút)")
        print(f"• Tổng số từ (VI + Term + EN): {words_vi + words_term + words_en} từ")
        print(f"• THỜI LƯỢNG DỰ KIẾN: {total_min:.1f} phút ({int(total_sec//60)} phút {int(total_sec%60)} giây)")

if __name__ == "__main__":
    asyncio.run(main())
