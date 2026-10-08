# Định dạng kịch bản podcast (từ 2026-10)

Mỗi bài có 2 tập, khoảng 20–30 phút/tập, gồm 3 phần với 3 chủ đề, đi từ dễ đến khó:

| Tập | Nội dung |
| :--- | :--- |
| **A** | Ôn nền → Khung bài → **Phần 1: Đời sống** (hội thoại, gọi điện, email, tin ngắn — từ vựng quen thuộc) → Tổng kết từ vựng |
| **B** | Ôn nhanh Tập A → **Phần 2: Đề thi** (y tế, giáo dục, xã hội, công nghệ, AI, văn hóa, trend) → Dùng lại cho chủ đề → **Phần 3: Bài hát** → Tổng kết từ vựng |

Đoạn tình huống được **viết riêng cho bài** sao cho chứa đủ các cấu trúc ngữ pháp của bài. Tin tức có thể cũ hoặc hư cấu, mục tiêu là ngữ pháp và từ vựng, không phải thông tin. Không chép nguyên văn bài báo thật.

## Thẻ (tag)

| Thẻ | Đọc bằng | Cách đọc |
| :--- | :--- | :--- |
| `[chapter] Tiêu đề` | — | Mốc chương trong ứng dụng podcast |
| `[vi] ...` | Giọng Việt | 1 lần |
| `[term] ...` | Giọng Anh nữ | 1 lần, nghỉ 0,5 giây |
| `[en] ...` | Giọng Anh nữ | 2 lần (chậm rồi thường) — câu đang phân tích |
| `[en2] ...` | Giọng Anh nam | 2 lần — câu của người nói thứ hai trong hội thoại |
| `[read] ...` | Giọng Anh nữ | 1 lần, tốc độ thường — đọc trọn đoạn |
| `[read2] ...` | Giọng Anh nam | 1 lần — lượt nói của người thứ hai khi đọc trọn hội thoại |
| `[song] Tên bài \| Ca sĩ` | — | Không đọc; dùng cho kiểm tra và ghi chú RSS |
| `[lyric] ...` | Giọng Anh nữ | 2 lần — tối đa 2 dòng mỗi bài hát, mỗi dòng ≤ 15 từ |

## Quy tắc bắt buộc (`scripts/check_script.py` kiểm tra)

1. **Không viết ký hiệu công thức** trong `[vi]`/`[term]`: `S`, `V`, `O`, `N`, `Adj`, `V2`, `V3`, `V-ing`, `V_bare`, `To-V`… TTS đọc thành chữ cái. Viết bằng lời: "chủ ngữ cộng động từ thêm ing", "động từ cột ba", "động từ nguyên mẫu".
2. **Không viết số bài dạng `1.1A`**. Viết "một chấm một, phần A".
3. **Đoạn tình huống đọc trọn 2 lần**: một lần trước khi phân tích, một lần sau khi phân tích. Mỗi dòng `[read]`/`[read2]` xuất hiện đúng 2 lần, ít nhất 6 câu.
4. **Chương phân tích có chữ "Mổ xẻ" trong tiêu đề.** Mỗi câu `[en]`/`[en2]` trong chương này phải có các dòng `[vi]` bắt đầu bằng:
   - `Ngữ pháp:` — cấu trúc, nói bằng lời.
   - `So sánh:` (với cấu trúc gần giống, khi nào dùng cái nào) **hoặc** `Bẫy:` (lỗi hay gặp trong đề).
   - `Từ vựng:` — tối đa 2 từ mới, kèm đồng nghĩa và cách phân biệt, họ từ nếu có.
5. **Chương bắt buộc**: Tập A có "Ôn nền", "Phần 1", "Mổ xẻ", "Từ vựng". Tập B có "Phần 2", "Mổ xẻ", "Dùng lại", "Phần 3", "Từ vựng".
6. **Bài hát (Phần 3)**: ít nhất 3 bài. Ưu tiên phân tích **tên bài hát** (tên bài không có bản quyền). Không đưa bản thu âm gốc vào audio. Nếu trích lời thì tối đa 2 dòng mỗi bài, luôn nêu tên bài và ca sĩ. Mỗi bài nên có một ý "trong bài hát thì được, trong bài thi thì không" nếu lời bài hát sai ngữ pháp chuẩn.

## Giới hạn mỗi câu (chống quá tải khi chỉ nghe)

1 điểm ngữ pháp + 1 so sánh + 1 bẫy (nếu có bẫy thật) + 2 từ mới với 1 nhóm đồng nghĩa.

## Khối mẫu

```
[vi] Câu số ba. Mai kể chuyện xe hỏng.
[en] My car broke down on the way home yesterday.
[vi] Ngữ pháp: quá khứ đơn, vì có mốc yesterday, việc đã xong hoàn toàn.
[term] broke down, yesterday
[vi] So sánh: nếu nói My car has broken down, không kèm yesterday, thì người nghe hiểu là xe đang hỏng ngay lúc này.
[vi] Bẫy: có yesterday mà dùng hiện tại hoàn thành là sai.
[vi] Từ vựng: break down là hỏng máy, dùng cho xe và máy móc. Còn break là vỡ, gãy, như break a glass.
[term] break down, break
```
