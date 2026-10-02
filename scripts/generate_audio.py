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

def get_audio_duration_ms(file_path):
    cmd = [
        FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
        "-of", "json", file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    return int(float(data["format"]["duration"]) * 1000)

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
            await asyncio.sleep(0.4)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error on chunk [{text[:30]}...]: {e}")
                raise e
            await asyncio.sleep(1.5)

async def build_episode(script_path, output_mp3_path, episode_title):
    print(f"\n============================================================")
    print(f"🎙️ BẮT ĐẦU SẢN XUẤT: {episode_title}")
    print(f"Script: {script_path} -> Output: {output_mp3_path}")
    print(f"============================================================")
    
    temp_dir = os.path.join("output", "temp_" + os.path.splitext(os.path.basename(script_path))[0])
    os.makedirs(temp_dir, exist_ok=True)
    
    # Silence templates
    f_silence_05s = os.path.join(temp_dir, "silence_05s.mp3")
    f_silence_10s = os.path.join(temp_dir, "silence_10s.mp3")
    f_silence_15s = os.path.join(temp_dir, "silence_15s.mp3")
    make_silence(0.5, f_silence_05s)
    make_silence(1.0, f_silence_10s)
    make_silence(1.5, f_silence_15s)
    dur_silence_05s = 500
    dur_silence_10s = 1000
    dur_silence_15s = 1500

    with open(script_path, encoding="utf-8") as f:
        lines = [l.strip() for l in f.read().split("\n") if l.strip()]

    # Parse tokens
    tokens = []
    current_chapter = "Mở đầu"
    for l in lines:
        if l.startswith("[chapter] "):
            current_chapter = l[10:].strip()
            tokens.append(("chapter", current_chapter))
        elif l.startswith("[vi] "):
            tokens.append(("vi", l[5:].strip()))
        elif l.startswith("[term] "):
            tokens.append(("term", l[7:].strip()))
        elif l.startswith("[en] "):
            tokens.append(("en", l[5:].strip()))

    chapters = []
    chunk_files = []
    chunk_durations = []
    
    current_chap_title = "Mở đầu"
    current_chap_start_ms = 0
    running_ms = 0
    
    idx = 0
    total_tokens = len(tokens)
    
    for tag, val in tokens:
        idx += 1
        if tag == "chapter":
            if current_chap_start_ms < running_ms:
                chapters.append({
                    "title": current_chap_title,
                    "start": current_chap_start_ms,
                    "end": running_ms
                })
            current_chap_title = val
            current_chap_start_ms = running_ms
            print(f"\n📑 Chương mới: {val} (bắt đầu tại {running_ms//1000}s)")
            continue
            
        print(f"[{idx}/{total_tokens}] [{tag}] {val[:40]}...")
        
        if tag == "vi":
            f_out = os.path.join(temp_dir, f"chunk_{idx:03d}_vi.mp3")
            await generate_chunk(val, VOICE_VI, None, f_out)
            d = get_audio_duration_ms(f_out)
            chunk_files.append(f_out)
            chunk_durations.append(d)
            running_ms += d
            
        elif tag == "term":
            f_out = os.path.join(temp_dir, f"chunk_{idx:03d}_term.mp3")
            await generate_chunk(val, VOICE_EN, None, f_out)
            d = get_audio_duration_ms(f_out)
            chunk_files.append(f_out)
            chunk_durations.append(d)
            running_ms += d
            
            # 0.5s pause after term
            chunk_files.append(f_silence_05s)
            chunk_durations.append(dur_silence_05s)
            running_ms += dur_silence_05s
            
        elif tag == "en":
            # EN Read 1 (0.9x) + 1.0s gap + EN Read 2 (1.0x) + 1.5s gap
            f_en1 = os.path.join(temp_dir, f"chunk_{idx:03d}_en1_slow.mp3")
            f_en2 = os.path.join(temp_dir, f"chunk_{idx:03d}_en2_norm.mp3")
            await generate_chunk(val, VOICE_EN, "-10%", f_en1)
            await generate_chunk(val, VOICE_EN, None, f_en2)
            
            d_en1 = get_audio_duration_ms(f_en1)
            d_en2 = get_audio_duration_ms(f_en2)
            
            chunk_files.append(f_en1)
            chunk_durations.append(d_en1)
            running_ms += d_en1
            
            chunk_files.append(f_silence_10s)
            chunk_durations.append(dur_silence_10s)
            running_ms += dur_silence_10s
            
            chunk_files.append(f_en2)
            chunk_durations.append(d_en2)
            running_ms += d_en2
            
            chunk_files.append(f_silence_15s)
            chunk_durations.append(dur_silence_15s)
            running_ms += dur_silence_15s

    # Finalize last chapter
    if current_chap_start_ms < running_ms:
        chapters.append({
            "title": current_chap_title,
            "start": current_chap_start_ms,
            "end": running_ms
        })

    # Step 2: Concatenate chunks
    print(f"\n[2/3] Đang ghép nối {len(chunk_files)} file âm thanh thành file hoàn chỉnh...")
    concat_list = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in chunk_files:
            clean_p = os.path.abspath(p).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    raw_mp3 = os.path.join(temp_dir, "raw_combined.mp3")
    cmd_concat = [
        FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-ar", "24000", "-ac", "1", "-b:a", "64k", raw_mp3
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)

    # Step 3: Write ID3 Chapters metadata
    print(f"[3/3] Đang gắn ID3 Chapters metadata ({len(chapters)} chapters)...")
    meta_path = os.path.join(temp_dir, "ffmetadata.txt")
    meta_lines = [
        ";FFMETADATA1",
        f"title={episode_title}",
        "artist=LMK89",
        "album=VSTEP B1-B2-C1 Thực Chiến (Audio Podcast)",
        "genre=Podcast",
        "comment=Chuỗi bài giảng podcast VSTEP chất lượng cao",
    ]
    for ch in chapters:
        meta_lines.extend([
            "[CHAPTER]",
            "TIMEBASE=1/1000",
            f"START={ch['start']}",
            f"END={ch['end']}",
            f"title={ch['title']}"
        ])
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write("\n".join(meta_lines))

    # Apply metadata to final MP3
    cmd_meta = [
        FFMPEG_BIN, "-y", "-i", raw_mp3, "-i", meta_path,
        "-map_metadata", "1", "-codec", "copy", output_mp3_path
    ]
    subprocess.run(cmd_meta, capture_output=True, check=True)
    
    final_dur_sec = get_audio_duration_ms(output_mp3_path) / 1000.0
    file_size_mb = os.path.getsize(output_mp3_path) / (1024 * 1024)
    print(f"\n🎉 HOÀN THÀNH: {output_mp3_path}")
    print(f"• Thời lượng: {final_dur_sec/60:.2f} phút ({int(final_dur_sec//60)} phút {int(final_dur_sec%60)} giây)")
    print(f"• Dung lượng: {file_size_mb:.2f} MB")
    print(f"• ID3 Chapters: {len(chapters)} chapters")

async def main():
    os.makedirs("output", exist_ok=True)
    
    # 1. Build Lesson 1.2A
    await build_episode(
        "podcast-scripts/script-1-2-a.txt",
        "output/lesson-1-2-a.mp3",
        "Bài 1.2A: Quy Tắc Phối Thì - Bản Chất Ngôn Ngữ & Từ Vựng Học Thuật"
    )
    
    # 2. Build Lesson 1.2B
    await build_episode(
        "podcast-scripts/script-1-2-b.txt",
        "output/lesson-1-2-b.mp3",
        "Bài 1.2B: Quy Tắc Phối Thì - Mổ Xẻ Bẫy Đề Thi & Kỹ Năng Writing/Speaking"
    )

if __name__ == "__main__":
    asyncio.run(main())

