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


## Chạy local (phát triển)

### Yêu cầu

- Python 3.11, Node.js 20, Docker Desktop, Git

### 1. Cấu hình

```bash
git clone ...
cd Space-Trace
cp .env.example .env
```

Mở `.env` và điền giá trị thật (JWT_SECRET, TOKEN_ENCRYPTION_KEY, mật khẩu DB, khóa S3, Google OAuth).

### 2. Chạy PostgreSQL và SeaweedFS

```bash
docker compose up -d
```

PostgreSQL mở ở cổng `5433`, SeaweedFS S3 ở cổng `8333`.

### 3. Chạy backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API chạy ở `http://localhost:8000`, tài liệu Swagger ở `http://localhost:8000/docs`. Lần đầu nhập ảnh, mô hình YOLO và OpenCLIP sẽ được tải về nên hơi lâu.

### 4. Chạy frontend

```bash
cd frontend
npm install
npm run dev
```

Mở địa chỉ Vite in ra (thường `http://localhost:5173`).

### 5. Google OAuth (để đăng nhập)

Trong Google Cloud Console, thêm vào OAuth client: JavaScript origin là địa chỉ frontend và redirect URI trùng `GOOGLE_REDIRECT_URI` trong `.env`. Bật Photos Picker API nếu muốn nhập ảnh từ Google Photos.

## Chạy bằng Docker (production)

Chạy toàn bộ hệ thống (PostgreSQL, SeaweedFS, migrate, 2 backend, web Nginx) bằng Docker Compose.

```bash
cp .env.example .env
cp .env.deploy.example .env.deploy
# điền giá trị thật vào .env, chọn khối local hoặc server trong .env.deploy
```

Các lệnh thường dùng (rút gọn bằng biến `C`):

```bash
C="docker compose -f docker-compose.prod.yml --env-file .env --env-file .env.deploy"

$C up -d --build   # build và chạy
$C ps              # xem trạng thái container
$C logs -f api1    # xem log backend
$C stop            # dừng, giữ dữ liệu
$C down            # xóa container, giữ dữ liệu
```

Sau khi chạy: ứng dụng ở `http://localhost:8080`, Swagger ở `http://localhost:8080/docs`.

> **Cảnh báo:** `down -v` xóa cả volume `pgdata` và `seaweeddata`, tức mất toàn bộ dữ liệu và ảnh. Không dùng trên server thật.

Trên server, web chỉ mở ở `127.0.0.1:8080`; dùng Caddy hoặc Nginx của máy chủ để bật HTTPS.
