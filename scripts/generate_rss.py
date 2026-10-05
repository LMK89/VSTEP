import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RELEASE_TAG = "v0.2.0-pilot"
BASE_URL = f"https://github.com/LMK89/VSTEP/releases/download/{RELEASE_TAG}"
SITE_URL = "https://lmk89.github.io/VSTEP/"

EPISODES = [
    {
        "id": "1-2-a",
        "title": "Bài 1.2A: Quy Tắc Phối Thì - Bản Chất Ngôn Ngữ & Từ Vựng Học Thuật",
        "file": "lesson-1-2-a.mp3",
        "duration": "17:22",
        "length_bytes": 8342141,
        "pub_date": "Fri, 02 Oct 2026 08:00:00 +0700",
        "description": "Tập 1.2A mổ xẻ bản chất ngữ pháp của các liên từ thời gian (When, While, Before, After, By the time, Since, As soon as, Until) cùng 14 câu ví dụ học thuật B2/C1 và bóc tách collocations ghi điểm."
    },
    {
        "id": "1-2-b",
        "title": "Bài 1.2B: Quy Tắc Phối Thì - Mổ Xẻ Bẫy Đề Thi & Kỹ Năng Writing/Speaking",
        "file": "lesson-1-2-b.mp3",
        "duration": "16:56",
        "length_bytes": 8131347,
        "pub_date": "Fri, 02 Oct 2026 08:30:00 +0700",
        "description": "Tập 1.2B vạch trần các cạm bẫy đổi giờ trong Listening Part 1/2 và Reading, hướng dẫn 17 câu ứng dụng trực tiếp vào Writing Task 1/2 và Speaking Part 2/3 kèm chuyên mục Tự hỏi Tự đáp."
    }
]

def generate_podcast_xml(out_path="podcast.xml"):
    items_xml = []
    for ep in EPISODES:
        mp3_url = f"{BASE_URL}/{ep['file']}"
        item = f"""    <item>
      <title><![CDATA[{ep['title']}]]></title>
      <description><![CDATA[{ep['description']}]]></description>
      <link>{SITE_URL}</link>
      <guid isPermaLink="false">{ep['id']}-{RELEASE_TAG}</guid>
      <pubDate>{ep['pub_date']}</pubDate>
      <enclosure url="{mp3_url}" length="{ep['length_bytes']}" type="audio/mpeg"/>
      <itunes:duration>{ep['duration']}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
      <itunes:episodeType>full</itunes:episodeType>
    </item>"""
        items_xml.append(item)

    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
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
    <itunes:type>episodic</itunes:type>
    <itunes:category text="Education">
      <itunes:category text="Language Learning"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="https://raw.githubusercontent.com/LMK89/VSTEP/main/data/podcast_cover.png"/>
{chr(10).join(items_xml)}
  </channel>
</rss>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rss_content)
    print(f"-> Đã sinh file RSS Podcast: {out_path} trỏ tới GitHub Releases tag {RELEASE_TAG}")

if __name__ == "__main__":
    generate_podcast_xml()
