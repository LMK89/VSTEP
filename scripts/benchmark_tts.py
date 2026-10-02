import asyncio
import os
import shutil
import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Locate FFmpeg
def get_ffmpeg_bin():
    if shutil.which("ffmpeg"):
        return "ffmpeg", "ffprobe"
    winget_path = r"C:\Users\khang.le\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
    ffmpeg = os.path.join(winget_path, "ffmpeg.exe")
    ffprobe = os.path.join(winget_path, "ffprobe.exe")
    if os.path.exists(ffmpeg):
        return ffmpeg, ffprobe
    raise RuntimeError("FFmpeg not found!")

FFMPEG_BIN, FFPROBE_BIN = get_ffmpeg_bin()

# Voice Constants
VOICE_VI = "vi-VN-NamMinhNeural"
VOICE_EN = "en-US-JennyNeural"

SAMPLE_VI_1 = """Chào mừng các bạn đến với chuỗi podcast ôn luyện VSTEP thực chiến. Trong tập hôm nay, chúng ta sẽ cùng nhau làm chủ quy tắc phối thì và mốc thời gian, một trong những chủ đề xuất hiện liên tục trong cả bốn kỹ năng thi."""

SAMPLE_EN_1 = """By the time the government introduced public smoking bans, tobacco usage had already caused millions of premature deaths."""

SAMPLE_VI_2 = """Trong câu vừa rồi, các bạn hãy đặc biệt lưu ý cụm từ premature deaths có nghĩa là những ca tử vong sớm, và cấu trúc by the time đi với thì quá khứ đơn, buộc vế còn lại phải lùi về quá khứ hoàn thành."""

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
        FFMPEG_BIN, "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec), "-c:a", "libmp3lame", "-b:a", "64k", out_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)

async def generate_chunk(text, voice, rate_str, out_path):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate_str)
    await comm.save(out_path)

async def main():
    os.makedirs("output/temp", exist_ok=True)
    
    f_vi1 = "output/temp/sample_vi1.mp3"
    f_en_slow = "output/temp/sample_en_slow.mp3"
    f_en_normal = "output/temp/sample_en_normal.mp3"
    f_vi2 = "output/temp/sample_vi2.mp3"
    
    f_silence_intro = "output/temp/silence_08s.mp3"
    f_silence_en_gap = "output/temp/silence_10s.mp3"
    f_silence_after_en = "output/temp/silence_15s.mp3"
    
    make_silence(0.8, f_silence_intro)
    make_silence(1.0, f_silence_en_gap)
    make_silence(1.5, f_silence_after_en)
    
    print("[1/3] Đang gọi edge-tts sinh các đoạn mẫu...")
    await generate_chunk(SAMPLE_VI_1, VOICE_VI, "+0%", f_vi1)
    await generate_chunk(SAMPLE_EN_1, VOICE_EN, "-10%", f_en_slow)
    await generate_chunk(SAMPLE_EN_1, VOICE_EN, "+0%", f_en_normal)
    await generate_chunk(SAMPLE_VI_2, VOICE_VI, "+0%", f_vi2)
    
    print("[2/3] Đo lường thời lượng từng đoạn...")
    dur_vi1 = get_audio_duration(f_vi1)
    dur_en_slow = get_audio_duration(f_en_slow)
    dur_en_normal = get_audio_duration(f_en_normal)
    dur_vi2 = get_audio_duration(f_vi2)
    
    # Concatenate using ffmpeg concat demuxer
    concat_list = "output/temp/concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in [f_vi1, f_silence_intro, f_en_slow, f_silence_en_gap, f_en_normal, f_silence_after_en, f_vi2]:
            clean_path = os.path.abspath(p).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")
            
    f_out = "output/sample_benchmark.mp3"
    cmd_concat = [
        FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-ar", "24000", "-ac", "1", "-b:a", "64k", f_out
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)
    total_dur = get_audio_duration(f_out)
    
    words_vi = len(SAMPLE_VI_1.split()) + len(SAMPLE_VI_2.split())
    dur_vi = dur_vi1 + dur_vi2
    wpm_vi = words_vi / (dur_vi / 60.0)
    
    words_en = len(SAMPLE_EN_1.split())
    dur_en_cycle = dur_en_slow + 1.0 + dur_en_normal + 1.5
    
    print(f"\n=======================================================")
    print(f"📊 KẾT QUẢ ĐO LƯỜNG TỐC ĐỘ ĐỌC (TTS BENCHMARK)")
    print(f"=======================================================")
    print(f"• Giọng tiếng Việt (NamMinhNeural):")
    print(f"  - Đoạn mẫu: {words_vi} từ | Thời lượng: {dur_vi:.2f} giây")
    print(f"  - Tốc độ đọc thực tế: {wpm_vi:.1f} từ/phút (wpm)")
    print(f"• Giọng tiếng Anh (JennyNeural) - 1 câu ({words_en} từ):")
    print(f"  - Lần 1 (0.9x): {dur_en_slow:.2f}s | Dừng: 1.0s")
    print(f"  - Lần 2 (1.0x): {dur_en_normal:.2f}s | Dừng: 1.5s")
    print(f"  - Tổng 1 chu kỳ câu tiếng Anh (2 lần + ngắt nghỉ): {dur_en_cycle:.2f} giây/câu (~{dur_en_cycle:.1f}s)")
    print(f"• File ghép mẫu (24 kHz, 64 kbps mono): {total_dur:.2f} giây")
    print(f"  -> Lưu tại: {os.path.abspath(f_out)}")

    # Compute Word Budget for Episode (14 - 21 mins, baseline: 12-14 English sentences)
    # Let's say an episode has 14 English sentences:
    num_en_sentences = 14
    en_total_time = num_en_sentences * dur_en_cycle
    
    print(f"\n=======================================================")
    print(f"🎯 NGÂN SÁCH CHỮ (WORD BUDGET) CHO 1 TẬP (MỤC TIÊU 15 - 20 PHÚT)")
    print(f"=======================================================")
    print(f"• Thời lượng cố định cho phần tiếng Anh ({num_en_sentences} câu, đọc 2 lần):")
    print(f"  = {num_en_sentences} câu x {dur_en_cycle:.1f}s = {en_total_time:.1f} giây (~{en_total_time/60:.1f} phút)")
    
    for target_min in [14, 15, 17, 20, 21]:
        target_sec = target_min * 60
        rem_sec_vi = target_sec - en_total_time
        target_words_vi = int((rem_sec_vi / 60) * wpm_vi)
        total_words = target_words_vi + (num_en_sentences * words_en)
        status = " (Cận dưới)" if target_min == 14 else " (Cận trên)" if target_min == 21 else " (Lý tưởng)" if target_min in (17, 18) else ""
        print(f"  - Mốc {target_min} phút{status}: Cần ~{target_words_vi} từ tiếng Việt + {num_en_sentences} câu tiếng Anh (~{num_en_sentences * words_en} từ) = Tổng ~{total_words} từ")

if __name__ == "__main__":
    asyncio.run(main())
