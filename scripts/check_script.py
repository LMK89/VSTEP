import sys

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
            # Check for duplicate [en]
            if i + 1 < len(lines) and lines[i+1].strip() == line:
                errors.append(f"Line {i+1}: Duplicate [en] line found.")
                has_error = True
                
        # Basic check if it has valid tags
        if not line.startswith('[') and not line.startswith('---') and line:
            errors.append(f"Line {i+1}: Line does not start with a tag: {line}")
            has_error = True
            
    if has_error:
        print(f"FAILED: {file_path}")
        for e in errors:
            print("  " + e)
    else:
        print(f"PASSED: {file_path} - No errors found.")
        
    return has_error

if __name__ == '__main__':
    files = ['podcast-scripts/script-1-2-a.txt', 'podcast-scripts/script-1-2-b.txt']
    err = False
    for file in files:
        if check_script(file):
            err = True
    if err:
        sys.exit(1)

