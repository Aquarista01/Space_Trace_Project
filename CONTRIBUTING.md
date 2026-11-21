# Đóng góp cho SpaceTrace

## Quy ước commit (Conventional Commits)

Định dạng: `type(scope): mô tả ngắn bằng tiếng Anh, viết thường, không dấu chấm cuối`

| Type | Dùng khi |
|---|---|
| `feat` | Thêm tính năng mới |
| `fix` | Sửa lỗi |
| `refactor` | Đổi cấu trúc code, không đổi hành vi |
| `test` | Thêm hoặc sửa test |
| `docs` | Chỉ sửa tài liệu |
| `chore` | Việc vặt: cấu hình, phụ thuộc, script |
| `ci` | Cấu hình CI (GitHub Actions) |

Ví dụ:

```
feat(objects): add favorite filter to GET /objects
fix(photos): return 502 when Google Picker fails
refactor(config): move AI match thresholds into Settings
test(backend): cover cosine_scores helper
docs(readme): add Docker production commands
chore(backend): pin dependency versions
```

Mỗi commit chỉ làm **một việc nhỏ** và chạy được.

## Nhánh

- `main` là nhánh chính, luôn ở trạng thái chạy được.


## Trước khi push

- Backend: `pytest` (khi đã có test).
- Frontend: `npm run build`.
- Docker: `bash scripts/prod.sh build` nếu đổi Dockerfile hoặc requirements.
- Không commit `.env`, `.env.deploy`, khóa hay mật khẩu thật.