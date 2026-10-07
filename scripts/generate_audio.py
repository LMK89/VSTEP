import asyncio
import os
import shutil
import subprocess
import json
import sys
import hashlib
import argparse
import logging
import glob

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/generate_audio.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_ffmpeg_bin():
    if shutil.which("ffmpeg"):
        return "ffmpeg", "ffprobe"
    winget_path = r"C:\Users\khang.le\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
    return os.path.join(winget_path, "ffmpeg.exe"), os.path.join(winget_path, "ffprobe.exe")

FFMPEG_BIN, FFPROBE_BIN = get_ffmpeg_bin()

VOICE_VI = "vi-VN-NamMinhNeural"
VOICE_EN = "en-US-JennyNeural"

CACHE_DIR = "output/.cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_audio_duration_ms(file_path):
    cmd = [
        FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
        "-of", "json", file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    return int(float(data["format"]["duration"]) * 1000)

def make_silence(duration_sec, out_path):
    if not os.path.exists(out_path):
        cmd = [
            FFMPEG_BIN, "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
            "-t", str(duration_sec), "-b:a", "64k", out_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

async def generate_chunk(text, voice, rate_str, out_path, sem, max_retries=3):
    import edge_tts
    # Determine cache hash
    hash_input = f"{text}_{voice}_{rate_str or ''}"
    chunk_hash = hashlib.md5(hash_input.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{chunk_hash}.mp3")
    
    if os.path.exists(cache_path):
        if out_path != cache_path:
            shutil.copy2(cache_path, out_path)
        return

    async with sem:
        for attempt in range(max_retries):
            try:
                if rate_str:
                    comm = edge_tts.Communicate(text, voice, rate=rate_str)
                else:
                    comm = edge_tts.Communicate(text, voice)
                await comm.save(out_path)
                
                # Copy to cache
                if out_path != cache_path:
                    shutil.copy2(out_path, cache_path)
                await asyncio.sleep(0.4)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Error on chunk [{text[:30]}...]: {e}")
                    raise e
                await asyncio.sleep(1.5)

def compute_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

async def process_episode(script_path, output_mp3_path, episode_title, sem):
    logging.info(f"BẮT ĐẦU SẢN XUẤT: {episode_title}")
    
    temp_dir = os.path.join("output", "temp_" + os.path.splitext(os.path.basename(script_path))[0])
    os.makedirs(temp_dir, exist_ok=True)
    
    f_silence_05s = os.path.join(CACHE_DIR, "silence_05s.mp3")
    f_silence_10s = os.path.join(CACHE_DIR, "silence_10s.mp3")
    f_silence_15s = os.path.join(CACHE_DIR, "silence_15s.mp3")
    make_silence(0.5, f_silence_05s)
    make_silence(1.0, f_silence_10s)
    make_silence(1.5, f_silence_15s)
    dur_silence_05s = 500
    dur_silence_10s = 1000
    dur_silence_15s = 1500

    with open(script_path, encoding="utf-8") as f:
        lines = [l.strip() for l in f.read().split("\n") if l.strip()]

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
    
    tasks = []
    task_metadata = []

    # First pass: Create generation tasks
    idx = 0
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
            continue
            
        if tag == "vi":
            f_out = os.path.join(temp_dir, f"chunk_{idx:03d}_vi.mp3")
            tasks.append(generate_chunk(val, VOICE_VI, None, f_out, sem))
            task_metadata.append(("single", f_out, None, None))
            
        elif tag == "term":
            f_out = os.path.join(temp_dir, f"chunk_{idx:03d}_term.mp3")
            tasks.append(generate_chunk(val, VOICE_EN, None, f_out, sem))
            task_metadata.append(("term", f_out, f_silence_05s, dur_silence_05s))
            
        elif tag == "en":
            f_en1 = os.path.join(temp_dir, f"chunk_{idx:03d}_en1_slow.mp3")
            f_en2 = os.path.join(temp_dir, f"chunk_{idx:03d}_en2_norm.mp3")
            tasks.append(generate_chunk(val, VOICE_EN, "-10%", f_en1, sem))
            tasks.append(generate_chunk(val, VOICE_EN, None, f_en2, sem))
            task_metadata.append(("en", f_en1, f_en2, None))

    logging.info(f"Generating {len(tasks)} audio chunks...")
    await asyncio.gather(*tasks)

    # Second pass: Compute durations & build timeline
    idx = 0
    for tag, val in tokens:
        if tag == "chapter":
            continue
            
        meta = task_metadata[idx]
        idx += 1
        
        if meta[0] == "single":
            f_out = meta[1]
            d = get_audio_duration_ms(f_out)
            chunk_files.append(f_out)
            running_ms += d
        elif meta[0] == "term":
            f_out = meta[1]
            f_silence = meta[2]
            d_silence = meta[3]
            d = get_audio_duration_ms(f_out)
            chunk_files.append(f_out)
            running_ms += d
            chunk_files.append(f_silence)
            running_ms += d_silence
        elif meta[0] == "en":
            f_en1 = meta[1]
            f_en2 = meta[2]
            d_en1 = get_audio_duration_ms(f_en1)
            d_en2 = get_audio_duration_ms(f_en2)
            
            chunk_files.append(f_en1)
            running_ms += d_en1
            chunk_files.append(f_silence_10s)
            running_ms += dur_silence_10s
            chunk_files.append(f_en2)
            running_ms += d_en2
            chunk_files.append(f_silence_15s)
            running_ms += dur_silence_15s

    if current_chap_start_ms < running_ms:
        chapters.append({
            "title": current_chap_title,
            "start": current_chap_start_ms,
            "end": running_ms
        })

    logging.info(f"Ghép nối {len(chunk_files)} files...")
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

    cmd_meta = [
        FFMPEG_BIN, "-y", "-i", raw_mp3, "-i", meta_path,
        "-map_metadata", "1", "-codec", "copy", output_mp3_path
    ]
    subprocess.run(cmd_meta, capture_output=True, check=True)
    
    final_duration = get_audio_duration_ms(output_mp3_path)
    if final_duration < 18 * 60 * 1000:
        logging.error(f"FAIL: {output_mp3_path} có thời lượng {(final_duration/1000)/60:.1f} phút (< 18 phút).")
        sys.exit(1)
        
    logging.info(f"HOÀN THÀNH: {output_mp3_path} ({(final_duration/1000)/60:.1f} phút)")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', type=int, help='Module number to build (1, 2, 3)')
    args = parser.parse_args()

    os.makedirs("output", exist_ok=True)
    hash_db_path = "output/.script_hashes.json"
    if os.path.exists(hash_db_path):
        with open(hash_db_path, "r", encoding="utf-8") as f:
            hash_db = json.load(f)
    else:
        hash_db = {}

    sem = asyncio.Semaphore(4)
    
    if args.module:
        scripts = sorted(glob.glob(f"podcast-scripts/script-{args.module}-*.txt"))
        for script in scripts:
            basename = os.path.basename(script)
            out_mp3 = f"output/lesson-{basename.replace('script-', '').replace('.txt', '')}.mp3"
            
            # Extract lesson logic: script-1-1-a.txt -> Bài 1.1A
            parts = basename.replace('script-', '').replace('.txt', '').split('-')
            if len(parts) >= 3:
                title = f"Bài {parts[0]}.{parts[1]}{parts[2].upper()}"
            else:
                title = f"Bài {basename}"

            current_hash = compute_file_hash(script)
            if os.path.exists(out_mp3) and hash_db.get(script) == current_hash:
                logging.info(f"SKIPPED: {script} (No changes detected)")
                continue

            await process_episode(script, out_mp3, title, sem)
            hash_db[script] = current_hash
            
            with open(hash_db_path, "w", encoding="utf-8") as f:
                json.dump(hash_db, f, indent=4)
    else:
        logging.info("Please specify --module argument")

if __name__ == "__main__":
    asyncio.run(main())
