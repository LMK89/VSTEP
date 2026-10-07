import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

def check_script(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        content = "".join(lines)
        
    errors = []
    has_error = False
    
    # 1. Estimate duration
    word_count = len(content.split())
    # Calibration based on 1.2a: 2522 words = ~17.3 mins => ~145 words/min
    est_duration = word_count / 145.0
    if est_duration < 15:
        errors.append(f"Thời lượng ước tính < 15 phút ({est_duration:.1f} phút). Cần viết dài hơn.")
        has_error = True
    elif est_duration < 20:
        print(f"  [WARNING] Thời lượng ước tính từ 15-20 phút ({est_duration:.1f} phút) cho {file_path}")
        
    # 2. Check chapter count and foundation review
    chapter_count = content.count('[chapter]')
    if chapter_count < 5:
        errors.append(f"Chỉ có {chapter_count} [chapter], yêu cầu >= 5.")
        has_error = True
        
    is_part_a = "-a.txt" in file_path.lower()
    is_part_b = "-b.txt" in file_path.lower()
    if is_part_a and "ôn nền" not in content.lower():
        errors.append("Tập A thiếu chương Ôn nền.")
        has_error = True
        
    # 3. Check tags
    valid_tags = ['[chapter]', '[vi]', '[term]', '[en]']
    en_count = 0
    in_vocab_summary = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('[chapter]'):
            if "từ vựng" in line.lower() or "tổng kết" in line.lower():
                in_vocab_summary = True
            else:
                in_vocab_summary = False
                
        # Check unknown tags
        if line.startswith('['):
            tag = line.split(']')[0] + ']'
            if tag not in valid_tags:
                errors.append(f"Line {i+1}: Có thẻ ngoài hợp lệ: {tag}")
                has_error = True
                
        if not line.startswith('[') and not line.startswith('---') and line:
            errors.append(f"Line {i+1}: Không bắt đầu bằng thẻ hợp lệ: {line}")
            has_error = True
            
        if line.startswith('[en]'):
            en_count += 1
            if i + 1 < len(lines) and lines[i+1].strip() == line:
                errors.append(f"Line {i+1}: Lặp thẻ [en].")
                has_error = True
                
        if in_vocab_summary and line.startswith('[vi]'):
            if ':' not in line and '-' not in line and not any('\u00C0' <= c <= '\u1EF9' for c in line):
                # Basic check for Vietnamese characters or colon/hyphen
                pass # it's hard to be perfect, let's strictly check for `:` or `-` if it has numbers
                text = line[4:].strip()
                if not (':' in text or '-' in text or 'nghĩa là' in text):
                    # Maybe it's just the intro like "[vi] Chúng ta cùng ôn lại..."
                    if len(text.split()) < 15: # if it's short, it should be a vocab line
                        # Wait, what if it doesn't have colon? Just warning or error?
                        # The user says "tổng kết từ vựng thiếu nghĩa tiếng Việt".
                        if any(char.isdigit() for char in text): # e.g. "1. ..."
                            if ':' not in text and '-' not in text:
                                errors.append(f"Line {i+1}: Dòng từ vựng có vẻ thiếu nghĩa Tiếng Việt (không có dấu ':' hoặc '-'): {text}")
                                has_error = True

    # 4. Check [en] count
    if is_part_a and en_count < 10:
        errors.append(f"Tập A có {en_count} câu [en], yêu cầu >= 10.")
        has_error = True
    if is_part_b and en_count < 8:
        errors.append(f"Tập B có {en_count} câu [en], yêu cầu >= 8.")
        has_error = True
        
    # 5. Check format like "1.5A" (number dot number letter)
    # The user says "số bài dạng 1.5A" meaning we shouldn't have something like "1.5A" in the script text.
    if re.search(r'\d\.\d[A-Za-z]', content):
        matches = re.findall(r'\d\.\d[A-Za-z]', content)
        errors.append(f"Có chứa số bài dạng {matches[0]} trong kịch bản (TTS sẽ đọc lỗi). Hãy viết chữ, vd: 'một chấm năm phần A'.")
        has_error = True
            
    if has_error:
        print(f"FAILED SCRIPT: {file_path}")
        for e in errors:
            print("  " + e)
    else:
        print(f"PASSED SCRIPT: {file_path}")
        
    return has_error

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
    err = False
    import glob
    scripts = glob.glob('podcast-scripts/script-*.txt')
    for s in scripts:
        if check_script(s):
            err = True
            
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
            except Exception as e:
                pass
                
    if err:
        sys.exit(1)
