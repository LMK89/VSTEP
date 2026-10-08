import os
import json
import re
import sys
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def parse_cards(card_file):
    if not os.path.exists(card_file):
        return []
    with open(card_file, encoding="utf-8") as f:
        content = f.read()
    
    raw_cards = re.split(r"===\s*CARD\s*\d+:\s*(.*?)\s*===", content)
    cards = []
    
    # raw_cards[0] is header/empty, then title, text, title, text...
    for i in range(1, len(raw_cards), 2):
        title = raw_cards[i].strip()
        body = raw_cards[i+1].strip() if i+1 < len(raw_cards) else ""
        
        grammar = ""
        synonyms = ""
        trap = ""
        
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("- Ngữ pháp:"):
                grammar = line.replace("- Ngữ pháp:", "").strip()
            elif line.startswith("+ Quá khứ:") or line.startswith("+ Tương lai:") or line.startswith("+ Hành động") or line.startswith("+ Mở rộng"):
                grammar += " " + line
            elif line.startswith("- Từ đồng nghĩa B2/C1:") or line.startswith("- Từ đồng nghĩa:"):
                synonyms = line.split(":", 1)[1].strip()
            elif line.startswith("- Bẫy đề thi:") or line.startswith("- Bẫy đề thi Reading:") or line.startswith("- Bẫy đề thi Listening:"):
                trap = line.split(":", 1)[1].strip()
                
        cards.append({
            "title": title,
            "grammar": grammar.strip(),
            "synonyms": synonyms.strip(),
            "exam_trap": trap.strip()
        })
    return cards

def generate_ics(all_cards, out_path):
    start_date = datetime.now() + timedelta(days=1)
    # Set to 08:00 AM
    start_date = start_date.replace(hour=8, minute=0, second=0, microsecond=0)
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//VSTEP B2-C1 Mastery Hub//Micro Learning//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:VSTEP 60s Micro-Learning",
        "X-WR-TIMEZONE:Asia/Ho_Chi_Minh"
    ]
    
    for idx, card in enumerate(all_cards):
        event_date = start_date + timedelta(days=idx)
        dt_start = event_date.strftime("%Y%m%dT%H%M%S")
        dt_end = (event_date + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")
        dt_stamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        
        desc = f"💡 BÀI: {card['title']}\\n\\n"
        desc += f"🧠 Ngữ pháp: {card['grammar']}\\n\\n"
        desc += f"🔄 Đồng nghĩa B2/C1: {card['synonyms']}\\n\\n"
        desc += f"⚠️ Bẫy đề thi: {card['exam_trap']}"
        
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:vstep-card-{idx+1}-{event_date.strftime('%Y%m%d')}@vstep.hub",
            f"DTSTAMP:{dt_stamp}",
            f"DTSTART:{dt_start}",
            f"DTEND:{dt_end}",
            f"SUMMARY:💡 VSTEP Ngày {idx+1}: {card['title']}",
            f"DESCRIPTION:{desc}",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:VSTEP 60s Check: {card['title']}",
            "TRIGGER:-PT0M",
            "END:VALARM",
            "END:VEVENT"
        ])
        
    lines.append("END:VCALENDAR")
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines))
    print(f"-> Đã sinh file lịch ICS: {out_path} ({len(all_cards)} thẻ, 8:00 sáng hàng ngày)")

def main():
    os.makedirs("data", exist_ok=True)
    
    cards_1_2 = parse_cards("podcast-scripts/cards-1-2.txt")
    
    data = {
        "version": "1.0.0",
        "title": "VSTEP B1-B2-C1 Mastery Hub",
        "updated_at": datetime.now().isoformat(),
        "modules": [
            {
                "id": "1-2",
                "name": "Quy Tắc Phối Thì & Mốc Thời Gian",
                "doc_path": "./docs/1-2-quy-tac-phoi-thi-va-moc-thoi-gian.md",
                "episodes": [
                    {
                        "id": "1-2-a",
                        "title": "Tập 1.2A: Email báo sự cố và 8 liên từ thời gian",
                        "audio_file": "lesson-1-2-a.mp3",
                        "duration_target": "20-30 mins",
                        "script_path": "./podcast-scripts/script-1-2-a.txt"
                    },
                    {
                        "id": "1-2-b",
                        "title": "Tập 1.2B: Bản tin học trực tuyến và học qua bài hát",
                        "audio_file": "lesson-1-2-b.mp3",
                        "duration_target": "20-30 mins",
                        "script_path": "./podcast-scripts/script-1-2-b.txt"
                    }
                ],
                "cards": cards_1_2
            }
        ]
    }
    
    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("-> Đã sinh master data.json")
    
    # Generate vstep_schedule.ics
    all_cards = []
    for m in data["modules"]:
        all_cards.extend(m["cards"])
    generate_ics(all_cards, "vstep_schedule.ics")

if __name__ == "__main__":
    main()
