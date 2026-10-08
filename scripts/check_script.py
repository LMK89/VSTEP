import sys
import os
import re
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

# Định dạng kịch bản: xem podcast-scripts/FORMAT.md
VALID_TAGS = ['[chapter]', '[vi]', '[term]', '[en]', '[en2]', '[read]', '[read2]', '[song]', '[lyric]']
EN_TAGS = ('[en]', '[en2]')
READ_TAGS = ('[read]', '[read2]')

# Ký hiệu công thức mà TTS sẽ đọc thành chữ cái ("ét", "vi"...). Phải viết bằng lời:
# "chủ ngữ", "động từ", "động từ cột ba", "động từ thêm ing", "động từ nguyên mẫu"...
ABBR_RE = re.compile(
    r"(?<![\w'’-])(?:V\(s/es\)|V_\w+|V-?ing|V-ed|V[0-3]|To-V|to-V|Adj|Adv|S|V|O|N)(?![\w'’-])"
)

MIN_READ_LINES = 6        # mỗi tập có ít nhất 1 đoạn tình huống >= 6 câu
MAX_LYRIC_PER_SONG = 2
MAX_LYRIC_WORDS = 15
MIN_SONGS = 3


def check_script(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        content = "".join(lines)

    errors = []
    warnings = []

    is_part_a = "-a.txt" in file_path.lower()
    is_part_b = "-b.txt" in file_path.lower()

    # 1. Ước lượng thời lượng
    word_count = len(content.split())
    # Calibration based on 1.2a: 2522 words = ~17.3 mins => ~145 words/min
    est_duration = word_count / 145.0
    if est_duration < 15:
        errors.append(f"Thời lượng ước tính < 15 phút ({est_duration:.1f} phút). Cần viết dài hơn.")
    elif est_duration < 20:
        warnings.append(f"Thời lượng ước tính từ 15-20 phút ({est_duration:.1f} phút).")
    elif est_duration > 32:
        warnings.append(f"Thời lượng ước tính > 32 phút ({est_duration:.1f} phút). Cân nhắc tách Tập C.")

    # 2. Chương bắt buộc
    chapters = [l.strip()[len('[chapter]'):].strip().lower() for l in lines if l.strip().startswith('[chapter]')]
    if len(chapters) < 5:
        errors.append(f"Chỉ có {len(chapters)} [chapter], yêu cầu >= 5.")

    def has_chapter(keyword):
        return any(keyword in c for c in chapters)

    required = []
    if is_part_a:
        required = ["ôn nền", "phần 1", "mổ xẻ", "từ vựng"]
    elif is_part_b:
        required = ["phần 2", "mổ xẻ", "dùng lại", "phần 3", "từ vựng"]
    for kw in required:
        if not has_chapter(kw):
            errors.append(f"Thiếu chương có chữ '{kw}' trong tiêu đề.")

    # 3. Duyệt từng dòng
    en_count = 0
    in_vocab_summary = False
    in_analysis = False
    read_lines = []
    current_song = None
    song_count = 0
    lyric_per_song = Counter()

    # khối phân tích: (dòng bắt đầu, câu, các dòng [vi] trong khối)
    blocks = []
    current_block = None

    def close_block():
        nonlocal current_block
        if current_block is not None:
            blocks.append(current_block)
            current_block = None

    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue

        if not line.startswith('[') and not line.startswith('---'):
            errors.append(f"Line {i+1}: Không bắt đầu bằng thẻ hợp lệ: {line}")
            continue
        if line.startswith('---'):
            continue

        tag = line.split(']')[0] + ']'
        if tag not in VALID_TAGS:
            errors.append(f"Line {i+1}: Có thẻ ngoài hợp lệ: {tag}")
            continue
        text = line[len(tag):].strip()

        if tag == '[chapter]':
            close_block()
            title = text.lower()
            in_vocab_summary = "từ vựng" in title or "tổng kết" in title
            in_analysis = "mổ xẻ" in title
            current_song = None
            continue

        # Ký hiệu công thức đọc sai
        if tag in ('[vi]', '[term]'):
            m = ABBR_RE.search(text)
            if m:
                errors.append(f"Line {i+1}: Có ký hiệu công thức '{m.group(0)}' (TTS đọc thành chữ cái). "
                              f"Viết bằng lời: chủ ngữ, động từ, động từ cột ba...")

        if tag in EN_TAGS:
            en_count += 1
            if i + 1 < len(lines) and lines[i+1].strip() == line:
                errors.append(f"Line {i+1}: Lặp thẻ {tag}.")
            if in_analysis:
                close_block()
                current_block = (i + 1, text, [])
            continue

        if tag in READ_TAGS:
            read_lines.append(line)
            continue

        if tag == '[song]':
            close_block()
            if '|' not in text or not all(p.strip() for p in text.split('|', 1)):
                errors.append(f"Line {i+1}: [song] phải có dạng 'Tên bài | Ca sĩ': {text}")
            current_song = text
            song_count += 1
            continue

        if tag == '[lyric]':
            if current_song is None:
                errors.append(f"Line {i+1}: [lyric] phải nằm sau một dòng [song].")
            else:
                lyric_per_song[current_song] += 1
                if lyric_per_song[current_song] > MAX_LYRIC_PER_SONG:
                    errors.append(f"Line {i+1}: Trích quá {MAX_LYRIC_PER_SONG} dòng lời của '{current_song}' (bản quyền).")
            if len(text.split()) > MAX_LYRIC_WORDS:
                errors.append(f"Line {i+1}: Dòng lời bài hát dài hơn {MAX_LYRIC_WORDS} từ (bản quyền).")
            continue

        if tag == '[vi]' and current_block is not None:
            current_block[2].append(text.lower())

        if in_vocab_summary and tag == '[vi]':
            if any(ch.isdigit() for ch in text[:3]) and ':' not in text and '-' not in text:
                errors.append(f"Line {i+1}: Dòng từ vựng có vẻ thiếu nghĩa Tiếng Việt (không có dấu ':' hoặc '-'): {text}")

    close_block()

    # 4. Mỗi câu trong chương "Mổ xẻ" phải đủ: Ngữ pháp, So sánh hoặc Bẫy, Từ vựng
    for start, sentence, vi_lines in blocks:
        missing = []
        if not any(v.startswith("ngữ pháp") for v in vi_lines):
            missing.append("Ngữ pháp")
        if not any(v.startswith("so sánh") or v.startswith("bẫy") for v in vi_lines):
            missing.append("So sánh/Bẫy")
        if not any(v.startswith("từ vựng") for v in vi_lines):
            missing.append("Từ vựng")
        if missing:
            errors.append(f"Line {start}: Câu '{sentence[:40]}...' thiếu dòng: {', '.join(missing)}.")

    # 5. Đoạn tình huống: đọc trọn ở đầu và đọc lại ở cuối => mỗi câu xuất hiện đúng 2 lần
    read_counter = Counter(read_lines)
    if len(read_counter) < MIN_READ_LINES:
        errors.append(f"Đoạn tình huống chỉ có {len(read_counter)} câu [read]/[read2], yêu cầu >= {MIN_READ_LINES}.")
    for l, n in read_counter.items():
        if n != 2:
            errors.append(f"Câu '{l[:50]}' xuất hiện {n} lần; mỗi câu đoạn tình huống phải đọc đúng 2 lần (đầu và cuối).")

    # 6. Số câu phân tích
    if is_part_a and en_count < 10:
        errors.append(f"Tập A có {en_count} câu [en]/[en2], yêu cầu >= 10.")
    if is_part_b and en_count < 8:
        errors.append(f"Tập B có {en_count} câu [en]/[en2], yêu cầu >= 8.")

    # 7. Bài hát (Tập B)
    if is_part_b and song_count < MIN_SONGS:
        errors.append(f"Phần bài hát có {song_count} [song], yêu cầu >= {MIN_SONGS}.")

    # 8. Số bài dạng "1.5A" (TTS đọc lỗi)
    matches = re.findall(r'\d\.\d[A-Za-z]', content)
    if matches:
        errors.append(f"Có chứa số bài dạng {matches[0]} trong kịch bản (TTS sẽ đọc lỗi). Hãy viết chữ, vd: 'một chấm năm phần A'.")

    if errors:
        print(f"FAILED SCRIPT: {file_path}")
        for e in errors:
            print("  " + e)
    else:
        print(f"PASSED SCRIPT: {file_path} ({est_duration:.1f} phút)")
    for w in warnings:
        print(f"  [WARNING] {w}")

    return bool(errors)


def check_docs(orig_path, new_path):
    with open(orig_path, 'r', encoding='utf-16') as f:
        orig_content = f.read()
    with open(new_path, 'r', encoding='utf-8') as f:
        new_content = f.read()

    orig_words = len(orig_content.split())
    new_words = len(new_content.split())
    orig_examples = orig_content.lower().count('ví dụ:') + orig_content.lower().count('ví dụ :')
    new_examples = new_content.lower().count('ví dụ:')

    errors = []
    has_error = False

    if new_words < orig_words * 0.95:
        errors.append(f"Word count decreased by >5% (Orig: {orig_words}, New: {new_words})")
        has_error = True
    if new_examples < orig_examples * 0.95:
        errors.append(f"Examples decreased by >5% (Orig: {orig_examples}, New: {new_examples})")
        has_error = True

    if has_error:
        print(f"FAILED DOCS: {new_path}")
        for e in errors:
            print("  " + e)
    else:
        print(f"PASSED DOCS: {new_path}")

    return has_error


if __name__ == '__main__':
    import glob
    err = False
    # Truyền file cụ thể để chỉ kiểm tra file đó; không truyền thì kiểm tra tất cả
    scripts = sys.argv[1:] or sorted(glob.glob('podcast-scripts/script-*.txt'))
    for s in scripts:
        if check_script(s):
            err = True

    if not sys.argv[1:]:
        docs_map = {
            '1.1': '1-1-cac-thi-trong-tam.md',
            '1.3': '1-3-danh-dong-tu-va-dong-tu-nguyen-mau.md',
            '1.4': '1-4-cau-bi-dong-co-ban-va-modals.md',
            '1.5': '1-5-cac-dang-so-sanh.md',
            '2.1': '2-1-menh-de-quan-he.md',
            '2.2': '2-2-ky-thuat-rut-gon-menh-de-quan-he.md',
            '2.3': '2-3-menh-de-nhuong-bo-va-nguyen-nhan.md',
            '2.4': '2-4-cau-dieu-kien-va-cau-truc-gia-dinh.md',
            '3.1': '3-1-cau-truc-de-xuat-tac-dong-ngan-chan.md',
            '3.2': '3-2-bi-dong-khach-quan-va-so-sanh-kep.md',
            '3.3': '3-3-dao-ngu-nang-cao-va-bo-lien-tu-dieu-huong.md'
        }
        for orig_id, new_name in docs_map.items():
            orig_path = f"docs/original/{orig_id}.md"
            new_path = f"docs/{new_name}"
            if os.path.exists(new_path) and os.path.exists(orig_path):
                try:
                    if check_docs(orig_path, new_path):
                        err = True
                except Exception:
                    pass

    if err:
        sys.exit(1)
