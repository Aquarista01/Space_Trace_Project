# SpaceTrace

SpaceTrace là ứng dụng web giúp bạn **biết đồ vật của mình đã được nhìn thấy lần cuối ở đâu và khi nào**, dựa trên ảnh bạn nhập từ Google Photos hoặc tải lên.

Hệ thống tự phát hiện đồ vật trong ảnh, nhận biết cùng một món đồ qua nhiều ảnh, gom ảnh theo từng căn phòng (Space) và so sánh hai thời điểm của một Space để thấy đồ nào mới xuất hiện, không còn được phát hiện hoặc đã đổi chỗ.

## Chức năng chính

- **Đăng nhập Google** và nhập ảnh từ Google Photos (Photos Picker) hoặc tải ảnh lên trực tiếp.
- **Phát hiện đồ vật** trong ảnh (80 lớp COCO).
- **Object History**: gom nhiều lần xuất hiện của cùng một món đồ thành một Object.
- **LastSeen**: lần cuối món đồ được thấy, ở Space nào.
- **Space**: nhóm ảnh theo căn phòng, có thể gộp hai Space.
- **RoomDiff**: so sánh hai thời điểm của một Space, kết quả gồm *Added*, *Not detected*, *Moved*. 

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| Cơ sở dữ liệu | PostgreSQL + pgvector |
| Lưu ảnh | SeaweedFS (S3 API) |
| Frontend | React, Vite, Tailwind CSS |
| AI phát hiện đồ vật | YOLOv8n (ultralytics) |
| AI nhận biết cùng đồ vật | OpenCLIP ViT-B-32 (vector 512 chiều) |
| Đóng gói | Docker Compose, Nginx |

## Kiến trúc tóm tắt

Trình duyệt (React) gọi REST API của FastAPI. Backend ghi dữ liệu vào PostgreSQL, ảnh vào SeaweedFS và chạy hai mô hình AI trên CPU khi nhập ảnh. Kiểu kiến trúc: client-server, SPA + REST API, backend nguyên khối.
