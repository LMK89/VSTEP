import asyncio
import os
import shutil
import hashlib
import subprocess
import logging
import re
import json
import edge_tts
import imageio_ffmpeg
import sys

sys.path.append('scripts')
import build_triet_podcast

DOCX_PATH = r"C:\Users\khang.le\Downloads\DAP_AN_CHI_TIET_10_CAU_ON_THI_TRIET_HOC-v2.docx"
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
CACHE_DIR = "output/.cache_triet_edge"
os.makedirs(CACHE_DIR, exist_ok=True)

async def synth_chunk_edge(text, voice="vi-VN-NamMinhNeural"):
    hash_key = hashlib.md5(f"{text}_{voice}_v2".encode("utf-8")).hexdigest()
    cache_file = os.path.join(CACHE_DIR, f"{hash_key}.mp3")
    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 1000:
        return cache_file

    rates = ["+0%", "+2%", "+5%", "-2%", "+3%"]
    endings = ["", ".", " "]
    cleaned = text.strip().rstrip(".")
    for r in rates:
        for end in endings:
            candidate = cleaned + end
            try:
                comm = edge_tts.Communicate(candidate, voice, rate=r)
                await comm.save(cache_file)
                if os.path.exists(cache_file) and os.path.getsize(cache_file) > 1000:
                    return cache_file
            except Exception:
                continue

    raise RuntimeError(f"Thất bại tổng hợp cho đoạn: {text[:50]}")

def make_silence(duration_sec: float, out_path: str):
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 200:
        cmd = [
            FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", str(duration_sec), "-b:a", "64k", out_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

def get_audio_duration_sec(file_path: str) -> float:
    cmd = [FFMPEG_BIN, "-i", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        h, mins, secs = int(m.group(1)), int(m.group(2)), float(m.group(3))
        return h * 3600 + mins * 60 + secs
    return 0.0

async def build_episodes():
    questions = build_triet_podcast.parse_docx(DOCX_PATH)
    f_sil_06 = os.path.join(CACHE_DIR, "sil_06.mp3")
    make_silence(0.6, f_sil_06)

    os.makedirs("output", exist_ok=True)
    target_questions = [q for q in questions if q["num"] in [2, 3]]
    
    # Read existing triet_data.json
    triet_data_path = "data/triet_data.json"
    with open(triet_data_path, "r", encoding="utf-8") as f:
        meta_list = json.load(f)

    for q in target_questions:
        num = q["num"]
        out_mp3 = f"output/triet-cau-{num:02d}.mp3"
        sections = build_triet_podcast.build_speech_sections_for_question(q)
        print(f"Bắt đầu render Câu {num} ({len(sections)} phần) bằng Edge TTS...")
        
        chunk_files = []
        for i, text in enumerate(sections):
            if not text.strip():
                continue
            c_path = await synth_chunk_edge(text)
            chunk_files.append(c_path)
            chunk_files.append(f_sil_06)
            print(f"  -> Đã render {i+1}/{len(sections)}: {text[:45]}...")

        concat_txt = os.path.join(CACHE_DIR, f"concat_cau_{num:02d}.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in chunk_files:
                abs_p = os.path.abspath(p).replace("\\", "/")
                f.write(f"file '{abs_p}'\n")

        # Chuẩn hóa âm lượng tự nhiên (không cần booster 2.4x gây rè)
        cmd = [
            FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-af", "volume=1.1,alimiter=limit=0.95",
            "-ar", "24000", "-ac", "1", "-b:a", "64k", out_mp3
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        dur = get_audio_duration_sec(out_mp3)
        mins = int(dur // 60)
        secs = int(dur % 60)
        dur_str = f"{mins:02d}:{secs:02d}"
        print(f"-> HOÀN THÀNH Câu {num}: {out_mp3} ({dur_str})")

        # Update metadata for this episode
        for item in meta_list:
            if item["num"] == num:
                item["duration"] = dur_str
                item["duration_sec"] = round(dur, 1)

    # Save updated json & bundle.js
    with open(triet_data_path, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, indent=2)

    # Also update docs_map for bundle
    docs_map = build_triet_podcast.write_markdown_files(questions)
    bundle_js = (
        "window.TRIET_DATA = "
        + json.dumps(meta_list, ensure_ascii=False, indent=2)
        + ";\nwindow.TRIET_DOCS = "
        + json.dumps(docs_map, ensure_ascii=False, indent=2)
        + ";\n"
    )
    with open("data/triet_bundle.js", "w", encoding="utf-8") as f:
        f.write(bundle_js)
    print("Cập nhật triet_data.json và triet_bundle.js thành công!")

if __name__ == "__main__":
    asyncio.run(build_episodes())
