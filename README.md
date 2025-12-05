# 🎨 ImageMagick WebGUI

Beautiful, powerful image processing in your browser. A production-ready web application for processing images using ImageMagick with a stunning, Notion-inspired user interface.

![ImageMagick WebGUI](https://img.shields.io/badge/ImageMagick-WebGUI-black?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)

## ✨ Features

### 🖼️ Image Processing
- **Resize & Crop**: Scale images by dimensions or percentage, with aspect ratio preservation
- **Format Conversion**: Convert between WebP, AVIF, JPEG, PNG, GIF, and more
- **Quality Control**: Fine-tune compression with quality slider (1-100%)
- **Filters & Effects**: Blur, sharpen, grayscale, sepia, brightness/contrast, saturation
- **Watermarking**: Add text overlays with customizable positioning
- **Rotate & Flip**: Transform orientation with preset or custom angles
- **Auto-Enhance**: One-click image enhancement using ImageMagick's auto-orient, enhance, and auto-level

### 🎯 User Interface
- **Ultra-clean design** inspired by Notion and modern design systems
- **Drag & drop** file upload with progress indicator
- **Beautiful gallery** with thumbnails and multi-select
- **Real-time command preview** showing exact ImageMagick commands
- **Terminal mode** for advanced users (Monaco editor with raw commands)
- **Dark/Light/System** theme support
- **Fully responsive** design for mobile and tablet
- **PWA support** - installable on desktop and mobile

### 🔒 Security
- **Whitelist-based** command validation
- **Path traversal protection**
- **Shell injection prevention**
- **Resource limits** (memory, CPU, timeout)
- **Rate limiting** for API endpoints
- **JWT authentication**

### ⚡ Performance
- **Background job processing** with Redis Queue
- **Progress tracking** for long-running operations
- **Batch processing** for multiple images
- **Optimized Docker image** (~250MB)
- **Auto cleanup** of temporary files

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB of RAM available

### One-Command Deployment

```bash
# Clone and start
git clone <repository-url>
cd imagemagick-webgui
docker compose up --build
```

That's it! The application will be available at:
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

### Environment Variables (Optional)

Create a `.env` file to customize settings:

```env
# Security (change in production!)
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET=your-jwt-secret-key-change-this

# Require login to use the app
REQUIRE_LOGIN=false

# Allow new user registration (set to false to disable signups)
ALLOW_REGISTRATION=true

# Google OAuth (optional - see setup instructions below)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Limits
MAX_UPLOAD_SIZE_MB=100
IMAGEMAGICK_TIMEOUT=30
IMAGEMAGICK_MEMORY_LIMIT=2GB
```

### Google OAuth Setup (Optional)

To enable "Sign in with Google":

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable OAuth APIs**
   - Go to "APIs & Services" > "Enabled APIs"
   - Enable "Google+ API" and "Google Identity"

3. **Create OAuth Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application"
   - Add authorized JavaScript origins:
     ```
     http://localhost:3000
     https://yourdomain.com
     ```
   - Add authorized redirect URIs:
     ```
     http://localhost:3000/api/auth/google/callback
     https://yourdomain.com/api/auth/google/callback
     ```
   - Copy Client ID and Client Secret

4. **Configure Environment**
   ```env
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

5. **Restart Application**
   ```bash
   docker compose down
   docker compose up --build
   ```

The "Continue with Google" button will automatically appear when OAuth is configured.

## 📖 Usage Guide

### Basic Workflow

1. **Upload Images**
   - Drag & drop files onto the upload zone
   - Or click to browse and select files
   - Supports: JPG, PNG, WebP, GIF, SVG, TIFF, PDF, HEIC, AVIF

2. **Select Images**
   - Click thumbnails to select/deselect
   - Use "Select All" for batch operations
   - Multi-select with checkboxes

3. **Choose Operations**
   - Use the sidebar to navigate operation categories
   - Configure parameters for each operation
   - Add multiple operations to build a pipeline

4. **Preview & Execute**
   - View the exact ImageMagick command before execution
   - Click "Apply to X image(s)" to process
   - Download results as ZIP

### Advanced: Terminal Mode

For power users, Terminal Mode provides direct access to ImageMagick:

```bash
# Example commands (use {input} and {output} as placeholders)
-resize 50% -quality 80
-blur 0x5 -modulate 110,120,100
-colorspace Gray -contrast
```

## 🏗️ Architecture

```
imagemagick-webgui/
├── docker-compose.yml      # Service orchestration
├── Dockerfile              # Multi-stage build
├── frontend/               # Next.js 15 + TypeScript
│   ├── app/               # App Router pages
│   ├── components/        # React components
│   │   ├── ui/           # shadcn/ui components
│   │   ├── layout/       # Layout components
│   │   └── features/     # Feature components
│   └── lib/              # Utilities, API client, store
├── backend/               # FastAPI + Python
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Config, database, security
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   └── workers/      # Background tasks
│   └── tests/            # Pytest tests
└── scripts/              # Startup scripts
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Zustand |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Queue | Redis + RQ (Redis Queue) |
| Database | PostgreSQL |
| Image Processing | ImageMagick 7 |
| Containerization | Docker, multi-stage builds |

## 🔧 Development

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest -v

# Frontend (if tests added)
cd frontend
npm test
```

## 📚 API Reference

### Authentication
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Login and get JWT
- `GET /api/auth/me` - Get current user

### Images
- `POST /api/images/upload` - Upload images (multipart)
- `GET /api/images` - List uploaded images
- `GET /api/images/{id}` - Get image file
- `GET /api/images/{id}/thumbnail` - Get thumbnail
- `DELETE /api/images/{id}` - Delete image

### Operations
- `POST /api/operations/process` - Process images
- `POST /api/operations/raw` - Process with raw command
- `POST /api/operations/preview-command` - Preview command
- `GET /api/operations/available` - List operations

### Queue
- `GET /api/queue/stats` - Queue statistics
- `GET /api/queue/jobs` - List jobs
- `GET /api/queue/jobs/{id}` - Job details
- `GET /api/queue/jobs/{id}/download` - Download results

Full API documentation available at `/docs` (Swagger UI) or `/redoc`.

## 🔐 Security Considerations

### Production Deployment

1. **Change all secrets** in environment variables
2. **Enable HTTPS** with a reverse proxy (nginx, traefik)
3. **Configure CORS** for your domain
4. **Set up proper backup** for PostgreSQL
5. **Monitor resource usage** and adjust limits

### Rate Limiting

Default limits:
- 100 requests/minute per IP
- 100MB max file size
- 30s timeout per ImageMagick operation
- 2GB memory limit per operation

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

## 🙏 Acknowledgments

- [ImageMagick](https://imagemagick.org/) - The powerful image processing library
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
- [Next.js](https://nextjs.org/) - The React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
