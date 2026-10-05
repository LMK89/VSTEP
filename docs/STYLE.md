# QUY CHUẨN ĐỊNH DẠNG TÀI LIỆU VSTEP (STYLE GUIDE)

Tất cả các tài liệu Markdown trong thư mục `docs/` đều phải tuân thủ nghiêm ngặt các quy tắc định dạng dưới đây để đảm bảo tính đồng nhất trên toàn hệ thống Web và Podcast.

## 1. Cấu Trúc File Cơ Bản
Mỗi bài học cần tuân theo trình tự sau:

1. **Heading 1 (`#`)**: Tên bài học. (VD: `# TÀI LIỆU HỌC TẬP CHI TIẾT BÀI 1.2: QUY TẮC PHỐI THÌ...`)
2. **Đường phân cách (`---`)**.
3. **Heading 2 (`## 0. ÔN NỀN NHANH (FOUNDATION REVIEW)`)**: Phần bắt buộc ở đầu mọi bài học. Gồm 1 đoạn dẫn nhập và 1 bảng tóm tắt công thức cốt lõi kèm ví dụ đời thường.
4. **Các Heading 2 (`## I...`, `## II...`)**: Các phần chính của bài.
5. **Heading 3 (`### 1...`, `### 2...`)**: Các mục con, ví dụ: bảng tổng hợp, các loại bẫy.
6. **Heading 4 (`#### ...`)**: Phân tích từng cấu trúc nhỏ (VD: `#### 1. Quy tắc phối thì với WHEN`).

## 2. Định Dạng Công Thức
- **Bắt buộc dùng Backticks (`` ` ``)** cho mọi công thức ngữ pháp thay vì LaTeX (`$...$`).
- VD: Không dùng `$S + V_{2/ed}$`, phải dùng `` `S + V_2/ed` ``.

## 3. Khối Ví Dụ (Ví dụ / Dịch / Từ vựng)
Mỗi cấu trúc cần có ít nhất 1 ví dụ minh họa trình bày theo thứ tự (dùng danh sách không đánh số `*`):
* **Ví dụ:** Câu tiếng Anh học thuật.
* **Dịch:** Bản dịch tiếng Việt sát nghĩa. Những từ vựng mục tiêu (B2/C1) nên được in nghiêng hoặc in đậm, và có giải thích cuối câu trong ngoặc đơn, in nghiêng. (VD: *(Từ vựng C1: emancipated - được giải phóng)*).

## 4. Định Dạng Bẫy Đề Thi
Khi cảnh báo một bẫy đề thi, sử dụng blockquote cảnh báo bằng biểu tượng `⚠️`:
> ⚠️ **Bẫy:** Thí sinh thường nghe mốc 5:15 sẽ chọn nhầm...

## 5. Bài Tập Trắc Nghiệm & Lời Giải
Phần bài tập áp dụng phải được đánh số thứ tự rõ ràng. Lời giải chi tiết bắt buộc phải ẩn đi bằng thẻ HTML `<details>`.

**Mẫu:**
**Câu 1:** She _______ her homework before she went to bed.
A. finished  
B. had finished  

<details>
<summary>Xem đáp án và giải thích</summary>
**Đáp án B**.  
**Giải thích:** Hành động "finish" xảy ra trước hành động "went to bed" trong quá khứ...
</details>
