# REST API Reference

Base URL: `http://localhost:8000`

Interactive documentation: [Swagger UI](http://localhost:8000/docs) | [ReDoc](http://localhost:8000/redoc)

---

## Authentication

### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Using Tokens
```http
Authorization: Bearer eyJ...
```

---

## Images

### Upload Images
```http
POST /api/images/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

files: [binary data]
```

Response:
```json
{
  "images": [
    {
      "id": 1,
      "original_filename": "photo.jpg",
      "stored_filename": "abc123.jpg",
      "file_path": "/app/uploads/abc123.jpg",
      "thumbnail_path": "/app/uploads/thumbnails/abc123_thumb.webp",
      "mime_type": "image/jpeg",
      "file_size": 1234567,
      "width": 1920,
      "height": 1080,
      "created_at": "2024-12-05T10:00:00Z"
    }
  ]
}
```

### List Images
```http
GET /api/images
Authorization: Bearer <token>
```

### Get Image
```http
GET /api/images/{id}
Authorization: Bearer <token>
```

### Download Image
```http
GET /api/images/{id}/download
```

### Delete Image
```http
DELETE /api/images/{id}
Authorization: Bearer <token>
```

---

## Operations

### Process Images (Synchronous)
```http
POST /api/operations/process-sync
Content-Type: application/json
Authorization: Bearer <token>

{
  "image_id": 1,
  "operations": [
    {"operation": "resize", "params": {"width": 800, "height": 600}},
    {"operation": "blur", "params": {"sigma": 5}}
  ],
  "output_format": "webp"
}
```

Response:
```json
{
  "success": true,
  "image_id": 2,
  "image_url": "/api/images/2"
}
```

### Process Multiple Images (Queue)
```http
POST /api/operations/process
Content-Type: application/json
Authorization: Bearer <token>

{
  "image_ids": [1, 2, 3],
  "operations": [
    {"operation": "resize", "params": {"percent": 50}}
  ],
  "output_format": "jpg",
  "quality": 85
}
```

Response:
```json
{
  "job_id": "job_abc123",
  "status": "queued"
}
```

### Preview Command
```http
POST /api/operations/preview-command
Content-Type: application/json

{
  "operations": [
    {"operation": "resize", "params": {"width": 800}}
  ],
  "output_format": "webp",
  "quality": 85
}
```

Response:
```json
{
  "command": "magick input.jpg -resize 800x -quality 85 output.webp"
}
```

### Execute Raw Command
```http
POST /api/operations/execute-raw
Content-Type: application/json
Authorization: Bearer <token>

{
  "image_id": 1,
  "command": "magick input.jpg -sepia-tone 80% output.jpg"
}
```

---

## AI Operations

### Remove Background
```http
POST /api/operations/remove-background-sync
Content-Type: application/json
Authorization: Bearer <token>

{
  "image_id": 1,
  "alpha_matting": true
}
```

Response:
```json
{
  "success": true,
  "image_id": 5,
  "image_url": "/api/images/5"
}
```

### Upscale Image
```http
POST /api/operations/upscale
Content-Type: application/json
Authorization: Bearer <token>

{
  "image_id": 1,
  "scale": 2
}
```

### AI Status
```http
GET /api/operations/ai-status
```

Response:
```json
{
  "available": true,
  "diagnostics": {
    "rembg_available": true,
    "pymatting_available": true,
    "models_found": ["u2net.onnx"]
  }
}
```

---

## Available Operations

| Operation | Parameters | Description |
|-----------|------------|-------------|
| `resize` | `width`, `height`, `percent`, `fit` | Resize image |
| `crop` | `x`, `y`, `width`, `height` | Crop region |
| `rotate` | `degrees` | Rotate (90, 180, 270) |
| `flip` | `direction` | `horizontal` or `vertical` |
| `blur` | `sigma` | Gaussian blur (1-30) |
| `sharpen` | `sigma` | Sharpen (0.5-5) |
| `brightness` | `value` | Brightness (50-150, 100=normal) |
| `contrast` | `value` | Contrast (50-150, 100=normal) |
| `saturation` | `value` | Saturation (0-200, 100=normal) |
| `hue` | `value` | Hue shift (-180 to 180) |
| `grayscale` | - | Convert to grayscale |
| `sepia-tone` | `threshold` | Sepia effect (0-100) |
| `watermark` | `text`, `position`, `font_size`, `opacity` | Add text watermark |
| `format` | `format` | Convert format |
| `quality` | `value` | Set quality (1-100) |
| `auto-orient` | - | Fix EXIF orientation |
| `enhance` | - | Auto-enhance |
| `auto-level` | - | Auto-level colors |

### Position Values (Watermark)
```
northwest  north  northeast
west       center east
southwest  south  southeast
```

---

## Queue

### Get Job Status
```http
GET /api/queue/jobs/{job_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "job_id": "job_abc123",
  "status": "completed",
  "progress": 100,
  "output_files": ["/app/processed/out1.jpg"],
  "created_at": "2024-12-05T10:00:00Z",
  "completed_at": "2024-12-05T10:00:05Z"
}
```

### List Jobs
```http
GET /api/queue/jobs
Authorization: Bearer <token>
```

---

## Health

### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "imagemagick": "7.1.1-21"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 413 | File Too Large |
| 422 | Validation Error |
| 500 | Server Error |
| 503 | Service Unavailable |

---

## Rate Limiting

Default limits:
- 100 requests/minute per IP
- 10 uploads/minute per user
- 5 concurrent processing jobs per user

Headers returned:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701777600
```
