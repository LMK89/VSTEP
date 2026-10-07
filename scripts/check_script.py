import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

def check_script(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    errors = []
    has_error = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('[en]'):
            if i + 1 < len(lines) and lines[i+1].strip() == line:
                errors.append(f"Line {i+1}: Duplicate [en] line found.")
                has_error = True
                
        if not line.startswith('[') and not line.startswith('---') and line:
            errors.append(f"Line {i+1}: Line does not start with a tag: {line}")
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
    
    # Simple word count
    orig_words = len(orig_content.split())
    new_words = len(new_content.split())
    
    orig_examples = orig_content.lower().count('ví dụ:') + orig_content.lower().count('ví dụ :')
    new_examples = new_content.lower().count('ví dụ:')
    
    errors = []
    has_error = False
    
    # Allow 5% margin
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
            
    # For docs, we check original vs new
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
