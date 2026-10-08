import os
import sys
import glob
import json
import subprocess
from datetime import datetime, timedelta
from urllib.parse import quote_plus

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RELEASE_TAG = "v0.4.0-module1"
BASE_URL = f"https://github.com/LMK89/VSTEP/releases/download/{RELEASE_TAG}"
SITE_URL = "https://lmk89.github.io/VSTEP/"

def get_ffmpeg_bin():
    import shutil
    if shutil.which("ffprobe"):
        return "ffprobe"
    winget_path = r"C:\Users\khang.le\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffprobe.exe"
    return winget_path

FFPROBE_BIN = get_ffmpeg_bin()

def get_audio_info(file_path):
    cmd = [
        FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
        "-of", "json", file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    duration = float(data["format"]["duration"])
    mins = int(duration // 60)
    secs = int(duration % 60)
    size = os.path.getsize(file_path)
    return f"{mins:02d}:{secs:02d}", size

def generate_podcast_xml(out_path="podcast.xml"):
    # Read scripts to get titles
    scripts = sorted(glob.glob("podcast-scripts/script-*.txt"))
    
    items_xml = []
    
    base_date = datetime.now() - timedelta(days=len(scripts) + 10)
    
    for idx, script_path in enumerate(scripts):
        basename = os.path.basename(script_path)
        # e.g. script-1-1-a.txt
        parts = basename.replace('script-', '').replace('.txt', '').split('-')
        ep_id = "-".join(parts)
        mp3_name = f"lesson-{ep_id}.mp3"
        mp3_path = os.path.join("output", mp3_name)
        
        if not os.path.exists(mp3_path):
            continue
            
        dur, size = get_audio_info(mp3_path)
        
        # Build Title
        title_str = f"Bài {parts[0]}.{parts[1]}{parts[2].upper()}"
            
        with open(script_path, 'r', encoding='utf-8') as f:
            all_lines = f.read().split('\n')
            first_lines = all_lines[:5]
            desc = f"Tập {parts[0]}.{parts[1]}{parts[2].upper()} của VSTEP Podcast."
            # try to find a chapter or vi
            for l in first_lines:
                if l.startswith('[vi]'):
                    desc = l[5:]
                    break
            # Bài hát được nhắc trong tập: chỉ ghi tên + ca sĩ + link tìm kiếm, không phát bản gốc
            songs = [l[len('[song]'):].strip() for l in all_lines if l.startswith('[song]')]
            if songs:
                song_items = []
                for s in songs:
                    title, artist = [p.strip() for p in s.split('|', 1)]
                    q = quote_plus(f"{title} {artist} official")
                    song_items.append(f'<li>{title} – {artist} (<a href="https://www.youtube.com/results?search_query={q}">nghe bản gốc</a>)</li>')
                desc += ("<p>Bài hát nhắc tới trong tập (chỉ phân tích tên bài, nghe bản gốc trên nền tảng chính thức):</p><ul>"
                         + "".join(song_items) + "</ul>")
        
        season = int(parts[0]) if len(parts) >= 1 else 1
        lesson = int(parts[1]) if len(parts) >= 2 else 1
        part_letter = parts[2].lower() if len(parts) >= 3 else 'a'
        episode_num = (lesson * 2) - (1 if part_letter == 'a' else 0)
        
        pub_date = (base_date + timedelta(days=idx)).strftime("%a, %d %b %Y %H:%M:%S +0700")
        
        mp3_url = f"https://github.com/LMK89/VSTEP/releases/download/{RELEASE_TAG}/{mp3_name}"
        
        item = f'''    <item>
      <title><![CDATA[{title_str}]]></title>
      <description><![CDATA[{desc}]]></description>
      <link>{SITE_URL}</link>
      <guid isPermaLink="false">{ep_id}-{RELEASE_TAG}</guid>
      <pubDate>{pub_date}</pubDate>
      <enclosure url="{mp3_url}" length="{size}" type="audio/mpeg"/>
      <itunes:duration>{dur}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:season>{season}</itunes:season>
      <itunes:episode>{episode_num}</itunes:episode>
    </item>'''
        items_xml.append(item)

    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" 
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title><![CDATA[VSTEP B1-B2-C1 Thực Chiến (Audio Podcast)]]></title>
    <link>{SITE_URL}</link>
    <language>vi</language>
    <itunes:author>LMK89</itunes:author>
    <description><![CDATA[Chuỗi Podcast bài giảng song ngữ mổ xẻ ngữ pháp thực chiến, bẫy phòng thi và cấu trúc ăn điểm Writing & Speaking cho kỳ thi VSTEP B1-B2-C1.]]></description>
    <itunes:summary><![CDATA[Chuỗi Podcast bài giảng song ngữ mổ xẻ ngữ pháp thực chiến, bẫy phòng thi và cấu trúc ăn điểm Writing & Speaking cho kỳ thi VSTEP B1-B2-C1.]]></itunes:summary>
    <itunes:type>serial</itunes:type>
    <itunes:category text="Education">
      <itunes:category text="Language Learning"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items_xml)}
  </channel>
</rss>'''

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rss_content)
    print(f"-> Đã sinh file RSS Podcast: {out_path} trỏ tới GitHub Releases tag {RELEASE_TAG}")

if __name__ == "__main__":
    generate_podcast_xml()
