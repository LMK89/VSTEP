import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

from gtts import gTTS
import imageio_ffmpeg

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

os.makedirs("logs", exist_ok=True)
os.makedirs("output/.cache_triet", exist_ok=True)
os.makedirs("docs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/build_triet.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

DOCX_PATH = "/Users/lekhang/Downloads/DAP_AN_CHI_TIET_10_CAU_ON_THI_TRIET_HOC-v2.docx"
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
CACHE_DIR = "output/.cache_triet"

SHORT_TITLES = {
    2: "Nguyên tắc phát triển & Sự vận dụng của C.Mác",
    3: "Lịch sử AI & Học thuyết Mâu thuẫn biện chứng",
    4: "Đấu tranh giữa Cái mới và Cái cũ (Liên hệ CNTT)",
    5: "Vai trò sáng tạo của Ý thức & Tác động của AI",
    6: "Nhận thức & Chân lý (Sai lầm hay Tích lũy chân lý)",
    7: "Thực tiễn là tiêu chuẩn duy nhất kiểm nghiệm Chân lý",
    8: "Vũ khí của sự phê phán & Mối quan hệ Vật chất - Ý thức",
    9: "Nguyên tắc thống nhất Lý luận và Thực tiễn trong CNTT",
    10: "Học thuyết Hình thái KT-XH & Quá trình lịch sử - tự nhiên",
    11: "So sánh phát minh của C.Darwin và K.Marx (Ph.Ăngghen)",
}


def clean_sentence_for_tts(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^[•📌✍️\-\+\*]+\s*", "", s)

    s = re.sub(r"\(\s*1\s*\)", " Một là, ", s)
    s = re.sub(r"\(\s*2\s*\)", " Hai là, ", s)
    s = re.sub(r"\(\s*3\s*\)", " Ba là, ", s)
    s = re.sub(r"\(\s*4\s*\)", " Bốn là, ", s)
    s = re.sub(r"\(\s*5\s*\)", " Năm là, ", s)

    s = s.replace("->", ", tiến lên ")
    s = s.replace("➔", ", tiến lên ")
    s = re.sub(r"\bvs\.?\b", " đối lập với ", s)
    s = s.replace(">55%", "trên 55 phần trăm")
    s = s.replace("%", " phần trăm")
    s = s.replace("&", " và ")
    s = s.replace("=", " tương ứng với ")
    s = s.replace(";", ".")
    s = s.replace(":", ".")

    s = re.sub(r"\(Mục 2 nhỏ III chương 2\)\s*", "", s)
    s = re.sub(r"\bAnh/Chị\b", "anh chị", s)

    replacements = [
        (r"\bPh\.?\s*Ăngghen\b", "Phri-đrích Ăng-ghen"),
        (r"\bC\.?\s*Mác\b", "Các Mác"),
        (r"\bK\.?\s*Marx\b", "Các Mác"),
        (r"\bKarl\s+Marx\b", "Các Mác"),
        (r"\bV\.?\s*I\.?\s*Lênin\b", "Lê-nin"),
        (r"\bLênin\b", "Lê-nin"),
        (r"\bC\.?\s*Darwin\b", "Sác-lơ Đác-uyn"),
        (r"\bCharles\s+Darwin\b", "Sác-lơ Đác-uyn"),
        (r"\bI\.?\s*Newton\b", "Niu-tơn"),
        (r"\bNewton\b", "Niu-tơn"),
        (r"\bA\.?\s*Einstein\b", "Anh-xtanh"),
        (r"\bEinstein\b", "Anh-xtanh"),
        (r"\bN\.?\s*Copernicus\b", "Cô-péc-ních"),
        (r"\bCopernicus\b", "Cô-péc-ních"),
        (r"\bPtolemy\b", "Ptô-lê-mê"),
        (r"\bD\.?\s*Hume\b", "Đê-vít Hium"),
        (r"\bHume\b", "Hium"),
        (r"\bI\.?\s*Kant\b", "Can-tơ"),
        (r"\bKant\b", "Can-tơ"),
        (r"\bL\.?\s*Feuerbach\b", "Phoi-ơ-bắc"),
        (r"\bFeuerbach\b", "Phoi-ơ-bắc"),
        (r"\bHegel\b", "Hê-ghen"),
        (r"\bAlan\s+Turing\b", "A-lan Tu-rinh"),
        (r"\bTuring\b", "Tu-rinh"),
        (r"\bDartmouth\b", "Đát-mớt"),
        (r"\bHighgate\b", "Hai-gết"),
        (r"\bPBCDV\b", "phép biện chứng duy vật"),
        (r"\bCNDV\b", "chủ nghĩa duy vật"),
        (r"\bCNTB\b", "chủ nghĩa tư bản"),
        (r"\bTBCN\b", "tư bản chủ nghĩa"),
        (r"\bCNXH\b", "chủ nghĩa xã hội"),
        (r"\bKT\s*-\s*XH\b", "kinh tế xã hội"),
        (r"\bQHSX\b", "quan hệ sản xuất"),
        (r"\bLLSX\b", "lực lượng sản xuất"),
        (r"\bCSHT\b", "cơ sở hạ tầng"),
        (r"\bKTTT\b", "kiến trúc thượng tầng"),
        (r"\bCMCN\s*4\.0\b", "cách mạng công nghiệp bốn chấm không"),
        (r"\bKHCN\b", "khoa học công nghệ"),
        (r"\bCNTT\b", "công nghệ thông tin"),
        (r"\b57-NQ/TW\b", "năm mươi bảy của Bộ Chính trị"),
        (r"\bNQ\s*57\b", "Nghị quyết năm mươi bảy"),
        (r"\b17/3/1883\b", "17 tháng 3 năm 1883"),
        (r"\b1960–1980\b", "1960 đến 1980"),
        (r"\b1960-1980\b", "1960 đến 1980"),
        (r"\bR&D\b", "nghiên cứu và phát triển"),
        (r"\bTFP\b", "năng suất nhân tố tổng hợp Tê Ép Pê"),
        (r"\bGDP\b", "Gê Đê Pê"),
        (r"\bPoC/MVP\b", "thử nghiệm bước đầu"),
        (r"\bMIS/API\b", "quản lý thông tin và giao diện lập trình"),
        (r"\bAI/OCR\b", "trí tuệ nhân tạo và nhận dạng chữ viết"),
        (r"\bGPU/RAM\b", "phần cứng đồ họa và bộ nhớ"),
        (r"\bVLM\b", "mô hình thị giác ngôn ngữ"),
        (r"\bVLMs\b", "các mô hình thị giác ngôn ngữ"),
        (r"\bLLMs\b", "các mô hình ngôn ngữ lớn"),
        (r"\bSLMs\b", "các mô hình ngôn ngữ nhỏ"),
        (r"\bOCR\b", "nhận dạng ký tự quang học"),
        (r"\bRAG\b", "tạo sinh tăng cường truy xuất"),
    ]

    for pat, rep in replacements:
        s = re.sub(pat, rep, s)

    s = re.sub(r"\(Artificial Intelligence\s*-\s*AI\)", "", s)
    s = re.sub(r"\(Agnosticism\)", "", s)
    s = re.sub(r"\(Retrieval-Augmented Generation\)", "", s)
    s = re.sub(r"\(Chain-of-Thought\)", "", s)
    s = re.sub(r"\(Quantization\)", "", s)
    s = re.sub(r"\(Knowledge Distillation\)", "", s)
    s = re.sub(r"\(Small Language Models\s*-\s*[^)]+\)", "", s)
    s = re.sub(r"\(Explainable AI\)", "", s)
    s = re.sub(r"\(Loss Function\)", "", s)
    s = re.sub(r"\(Backpropagation\)", "", s)
    s = re.sub(r"\(Epoch\)", "", s)
    s = re.sub(r"\(Weights\)", "", s)
    s = re.sub(r"\(Automated Testing\)", "", s)
    s = re.sub(r"\(Legacy Systems\)", "", s)
    s = re.sub(r"\(Domain Knowledge\)", "", s)
    s = re.sub(r"\(Domain Requirement\)", "", s)
    s = re.sub(r"\(refactoring\)", "", s)
    s = re.sub(r"\(scalability\)", "", s)

    s = s.replace("'", "").replace("“", "").replace("”", "").replace('"', "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_docx(docx_path: str):
    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read("word/document.xml")
    tree = ET.fromstring(xml_content)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    body = tree.find("w:body", ns)

    questions = []
    cur_q = None

    for elem in body:
        tag = elem.tag.split("}")[-1]
        if tag == "p":
            t = "".join([x.text for x in elem.findall(".//w:t", ns) if x.text]).strip()
            if not t:
                continue
            m = re.match(r"^CÂU\s+(\d+)\s*:\s*(.*)", t)
            if m:
                if cur_q:
                    questions.append(cur_q)
                cur_q = {
                    "num": int(m.group(1)),
                    "question": m.group(2).strip(),
                    "part1": [],
                    "part2": [],
                }
            elif cur_q:
                if "PHẦN 2:" in t:
                    continue
                cur_q["part2"].append(t)
        elif tag == "tbl" and cur_q:
            for p in elem.findall(".//w:p", ns):
                t = "".join([x.text for x in p.findall(".//w:t", ns) if x.text]).strip()
                if t and "PHẦN 1:" not in t:
                    cur_q["part1"].append(t)

    if cur_q:
        questions.append(cur_q)
    return questions


def write_markdown_files(questions):
    docs_map = {}
    for q in questions:
        num = q["num"]
        short_title = SHORT_TITLES.get(num, f"Câu {num}")
        md_lines = [
            f"# 🎓 CÂU {num}: {short_title}",
            "",
            f"> **Đề bài:** {q['question']}",
            "",
            "---",
            "",
            "## 📌 PHẦN 1: SƯỜN Ý CHÍNH – NẮM KHUNG & HỌC TRƯỚC KEYWORD",
            "",
        ]
        for item in q["part1"]:
            clean_item = re.sub(r"^[•\-\*]\s*", "", item)
            if ":" in clean_item:
                head, rest = clean_item.split(":", 1)
                md_lines.append(f"- **{head.strip()}:** {rest.strip()}")
            else:
                md_lines.append(f"- {clean_item}")

        md_lines.extend(
            [
                "",
                "---",
                "",
                "## ✍️ PHẦN 2: ĐÁP ÁN CHI TIẾT – HỌC THUỘC ĐỂ VIẾT BÀI THI TỰ LUẬN (ĐỀ ĐÓNG)",
                "",
            ]
        )

        for para in q["part2"]:
            if ":" in para:
                head, rest = para.split(":", 1)
                if len(head) < 120:
                    md_lines.append(f"### {head.strip()}")
                    md_lines.append("")
                    md_lines.append(rest.strip())
                    md_lines.append("")
                    continue
            md_lines.append(para)
            md_lines.append("")

        slug = f"triet-cau-{num:02d}"
        md_text = "\n".join(md_lines)
        docs_map[slug] = md_text
        md_path = f"docs/{slug}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
    return docs_map


def make_silence(duration_sec: float, out_path: str):
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 200:
        cmd = [
            FFMPEG_BIN,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            str(duration_sec),
            "-b:a",
            "64k",
            out_path,
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


def synth_gtts(text: str) -> str:
    """Tạo audio qua Google TTS - cực kỳ ổn định, to rõ, không giới hạn độ dài."""
    hash_key = hashlib.md5(f"{text}|gtts_v1".encode("utf-8")).hexdigest()
    cache_file = os.path.join(CACHE_DIR, f"{hash_key}.mp3")
    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 500:
        return cache_file

    if os.path.exists(cache_file):
        os.remove(cache_file)

    for attempt in range(5):
        try:
            tts = gTTS(text, lang="vi", slow=False)
            tts.save(cache_file)
            if os.path.exists(cache_file) and os.path.getsize(cache_file) > 500:
                time.sleep(0.2)
                return cache_file
        except Exception as e:
            logging.warning(f"Lỗi gTTS lần {attempt+1}/5 [{text[:35]}...]: {e}")
            if os.path.exists(cache_file):
                os.remove(cache_file)
        time.sleep(1.0 * (attempt + 1))

    raise RuntimeError(f"Thất bại tạo audio cho đoạn: {text[:50]}")


def build_speech_sections_for_question(q: dict):
    num = q["num"]
    short_title = SHORT_TITLES.get(num, f"Câu {num}")

    sections = []
    # 1. Đề bài
    sections.append(clean_sentence_for_tts(f"Ôn thi Triết học Cao học. Câu số {num}. {short_title}."))
    sections.append(clean_sentence_for_tts(f"Đề bài. {q['question']}."))

    # 2. Phần 1: Sườn ý chính
    sections.append(clean_sentence_for_tts(f"Phần một. Sườn ý chính và từ khóa cốt lõi của Câu {num}."))
    for item in q["part1"]:
        clean_item = re.sub(r"^[•\-\*]\s*", "", item)
        clean_item = re.sub(r"^(\d+)\.\s*", r"Ý chính số \1. ", clean_item)
        sections.append(clean_sentence_for_tts(clean_item))

    # 3. Phần 2: Đáp án chi tiết
    sections.append(clean_sentence_for_tts("Phần hai. Đáp án phân tích chi tiết để viết bài thi tự luận đề đóng."))

    recap_heads = []
    for para in q["part2"]:
        if ":" in para:
            head, body = para.split(":", 1)
            if len(head) < 130:
                head_clean = head.strip()
                m_num = re.match(r"^(\d+)\.\s*(.*)", head_clean)
                if m_num:
                    idx_num = m_num.group(1)
                    title_only = m_num.group(2)
                    recap_heads.append(f"Mục {idx_num}, {title_only}")
                    sections.append(clean_sentence_for_tts(f"Luận điểm số {idx_num}. {title_only}."))
                else:
                    sections.append(clean_sentence_for_tts(f"{head_clean}."))
                sections.append(clean_sentence_for_tts(body))
                continue
        sections.append(clean_sentence_for_tts(para))

    # 4. Chốt lại
    if recap_heads:
        recap_str = ". ".join(recap_heads)
        sections.append(
            clean_sentence_for_tts(
                f"Tổng kết lại Câu số {num}, khi vào phòng thi anh chị cần viết đủ {len(recap_heads)} mục lớn là. {recap_str}."
            )
        )

    return sections


def build_all():
    questions = parse_docx(DOCX_PATH)
    docs_map = write_markdown_files(questions)

    f_sil_06 = os.path.join(CACHE_DIR, "sil_06.mp3")
    make_silence(0.6, f_sil_06)

    os.makedirs("output", exist_ok=True)
    metadata_list = []

    for q in questions:
        num = q["num"]
        out_mp3 = f"output/triet-cau-{num:02d}.mp3"
        sections = build_speech_sections_for_question(q)

        logging.info(f"Đang tạo Audio cho Câu {num} ({len(sections)} phần)...")
        chunk_files = []
        for text in sections:
            if not text.strip():
                continue
            c_path = synth_gtts(text)
            chunk_files.append(c_path)
            chunk_files.append(f_sil_06)

        concat_txt = os.path.join(CACHE_DIR, f"concat_cau_{num:02d}.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in chunk_files:
                abs_p = os.path.abspath(p).replace("\\", "/")
                f.write(f"file '{abs_p}'\n")

        # Khuếch đại âm lượng to rõ X2.5 bằng ffmpeg
        cmd = [
            FFMPEG_BIN,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_txt,
            "-af",
            "volume=2.4,alimiter=limit=0.95",
            "-ar",
            "24000",
            "-ac",
            "1",
            "-b:a",
            "64k",
            out_mp3,
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        dur_sec = get_audio_duration_sec(out_mp3)
        mins = int(dur_sec // 60)
        secs = int(dur_sec % 60)
        dur_str = f"{mins:02d}:{secs:02d}"
        logging.info(f"-> HOÀN THÀNH Câu {num}: {out_mp3} ({dur_str})")

        metadata_list.append(
            {
                "num": num,
                "slug": f"triet-cau-{num:02d}",
                "short_title": SHORT_TITLES.get(num, f"Câu {num}"),
                "question": q["question"],
                "audio_file": f"./output/triet-cau-{num:02d}.mp3",
                "doc_file": f"./docs/triet-cau-{num:02d}.md",
                "duration": dur_str,
                "duration_sec": round(dur_sec, 1),
                "part1": q["part1"],
            }
        )

    with open("data/triet_data.json", "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, ensure_ascii=False, indent=2)

    bundle_js = (
        "window.TRIET_DATA = "
        + json.dumps(metadata_list, ensure_ascii=False, indent=2)
        + ";\nwindow.TRIET_DOCS = "
        + json.dumps(docs_map, ensure_ascii=False, indent=2)
        + ";\n"
    )
    with open("data/triet_bundle.js", "w", encoding="utf-8") as f:
        f.write(bundle_js)

    logging.info("TẤT CẢ 10 CÂU TRIẾT HỌC ĐÃ HOÀN TẤT THÀNH CÔNG!")


if __name__ == "__main__":
    build_all()
