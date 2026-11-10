#!/usr/bin/env bash
set -e

echo "Đang theo dõi tiến trình build Triết học..."
while pgrep -f "build_triet_podcast.py" > /dev/null; do
    sleep 10
done

echo "Tiến trình build_triet_podcast.py đã hoàn tất!"
cd /Users/lekhang/Documents/VSTEP

# Cập nhật bundle JS và commit toàn bộ code & dữ liệu
git add docs/triet-cau-*.md scripts/build_triet_podcast.py data/triet_data.json data/triet_bundle.js index.html logs/build_triet.log || true

if git status -s | grep -q .; then
    git commit -m "feat(triet): hoàn thành 10 tập podcast triết học cao học và dữ liệu bundle"
    git push origin main || true
    echo "Đã commit và push code lên GitHub thành công!"
else
    echo "Không có thay đổi mới cần commit."
fi

echo "ALL DONE!"

