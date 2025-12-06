# Architecture

System design and technical architecture of ImageMagick WebGUI.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Container                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Nginx (optional)                       │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────┴──────────────────────────────────┐  │
│  │                                                           │  │
│  │  ┌─────────────┐              ┌─────────────────────┐    │  │
│  │  │  Next.js    │◄────────────►│     FastAPI         │    │  │
│  │  │  Frontend   │    REST      │     Backend         │    │  │
│  │  │  :3000      │              │     :8000           │    │  │
│  │  └─────────────┘              └──────────┬──────────┘    │  │
│  │                                          │               │  │
│  │                          ┌───────────────┼───────────────┤  │
│  │                          │               │               │  │
│  │                          ▼               ▼               │  │
│  │                   ┌───────────┐   ┌───────────┐         │  │
│  │                   │PostgreSQL │   │   Redis   │         │  │
│  │                   │   :5432   │   │   :6379   │         │  │
│  │                   └───────────┘   └─────┬─────┘         │  │
│  │                                         │               │  │
│  │                                         ▼               │  │
│  │                                  ┌───────────┐          │  │
│  │                                  │ RQ Worker │          │  │
│  │                                  └───────────┘          │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    ImageMagick CLI                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    File System                            │  │
│  │  /app/uploads    /app/processed    /tmp                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### Frontend (Next.js 15)

**Technology Stack:**
- Next.js 15 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Zustand (state management)
- React Query (data fetching)

**Responsibilities:**
- User interface rendering
- Client-side routing
- Form handling
- Real-time preview
- File upload handling

**Key Files:**
```
frontend/
├── app/                 # Next.js App Router
│   ├── page.tsx        # Dashboard
│   ├── login/          # Auth pages
│   ├── settings/       # Settings page
│   └── history/        # History page
├── components/
│   ├── features/       # Feature components
│   ├── layout/         # Layout components
│   └── ui/             # UI primitives
└── lib/
    ├── api.ts          # API client
    ├── store.ts        # Zustand store
    └── utils.ts        # Utilities
```

### Backend (FastAPI)

**Technology Stack:**
- FastAPI (Python 3.12)
- SQLAlchemy (async)
- Pydantic (validation)
- Redis Queue (RQ)
- ImageMagick (CLI)
- rembg (AI)

**Responsibilities:**
- REST API endpoints
- Authentication/authorization
- Image processing orchestration
- Database operations
- Background job management

**Key Files:**
```
backend/
├── app/
│   ├── main.py         # FastAPI app
│   ├── api/            # API routes
│   │   ├── auth.py
│   │   ├── images.py
│   │   └── operations.py
│   ├── core/           # Core modules
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/         # SQLAlchemy models
│   ├── services/       # Business logic
│   │   ├── imagemagick.py
│   │   ├── ai_service.py
│   │   └── file_service.py
│   └── workers/        # Background tasks
└── requirements.txt
```

### Database (PostgreSQL)

**Schema:**
```sql
Users
├── id (PK)
├── email (unique)
├── password_hash
├── name
└── created_at

Images
├── id (PK)
├── user_id (FK → Users)
├── original_filename
├── stored_filename
├── file_path
├── thumbnail_path
├── mime_type
├── file_size
├── width
├── height
└── created_at

Jobs
├── id (PK)
├── job_id (unique)
├── user_id (FK → Users)
├── operation
├── status
├── progress
├── input_files
├── output_files
├── parameters
├── error_message
├── created_at
└── completed_at

Settings
├── id (PK)
├── user_id (FK → Users)
├── theme
├── default_format
├── default_quality
└── updated_at
```

### Queue (Redis + RQ)

**Purpose:**
- Background job processing
- Long-running operations
- Job status tracking

**Flow:**
```
1. API receives request
2. Job created in database
3. Task enqueued to Redis
4. Worker picks up task
5. ImageMagick processes image
6. Result saved
7. Job status updated
8. Client notified
```

### ImageMagick Service

**Responsibilities:**
- Build safe commands
- Execute with limits
- Handle errors
- Create thumbnails

**Security:**
- Command whitelist
- Path validation
- Resource limits
- Timeout enforcement

```python
ALLOWED_OPERATIONS = [
    "resize", "crop", "rotate", "flip",
    "blur", "sharpen", "brightness-contrast",
    "sepia-tone", "grayscale", "watermark",
    # ... more
]

RESOURCE_LIMITS = {
    "memory": "2GB",
    "timeout": 60,
    "disk": "4GB"
}
```

---

## Data Flow

### Image Upload

```
Browser                 Frontend              Backend               Storage
   │                       │                     │                     │
   │──POST /upload────────►│                     │                     │
   │                       │──POST /api/images──►│                     │
   │                       │                     │──validate file─────►│
   │                       │                     │◄─────────OK─────────│
   │                       │                     │──generate thumb────►│
   │                       │                     │──save to DB────────►│
   │◄──────────────────────│◄───image data──────│                     │
```

### Image Processing

```
Browser                 Frontend              Backend              Worker
   │                       │                     │                    │
   │──process request─────►│                     │                    │
   │                       │──POST /api/process─►│                    │
   │                       │                     │──create job───────►│
   │                       │                     │──enqueue task─────►│
   │                       │◄──job_id───────────│                    │
   │◄──job_id──────────────│                     │                    │
   │                       │                     │                    │
   │                       │                     │   ┌────────────────┤
   │                       │                     │   │ ImageMagick    │
   │                       │                     │   │ processes      │
   │                       │                     │   └────────────────┤
   │                       │                     │◄──result──────────│
   │──poll status─────────►│──GET /api/jobs/{id}►│                    │
   │◄──complete────────────│◄───────────────────│                    │
```

---

## Security Architecture

### Layers

```
┌─────────────────────────────────────┐
│         Rate Limiting               │
├─────────────────────────────────────┤
│         Authentication              │
├─────────────────────────────────────┤
│         Input Validation            │
├─────────────────────────────────────┤
│         Path Validation             │
├─────────────────────────────────────┤
│         Command Whitelist           │
├─────────────────────────────────────┤
│         Resource Limits             │
└─────────────────────────────────────┘
```

### Authentication Flow

```
1. User credentials → Backend
2. Validate credentials
3. Generate JWT token
4. Return token to client
5. Client stores token
6. Token sent with requests
7. Backend validates token
8. Access granted/denied
```

---

## Deployment Architecture

### Docker Compose

```yaml
services:
  app:        # Combined frontend + backend
  db:         # PostgreSQL
  redis:      # Queue backend
  worker:     # RQ worker
```

### Volumes

```yaml
volumes:
  postgres_data:    # Database persistence
  uploads:          # User uploads
  processed:        # Output files
```

### Networks

```yaml
networks:
  app_network:      # Internal communication
```

---

## Scalability Considerations

### Horizontal Scaling

```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
    │  App 1  │     │  App 2  │     │  App 3  │
    └────┬────┘     └────┬────┘     └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         ┌────▼────┐          ┌─────▼─────┐
         │   DB    │          │   Redis   │
         │(Primary)│          │ (Cluster) │
         └─────────┘          └───────────┘
```

### Bottlenecks

| Component | Bottleneck | Solution |
|-----------|------------|----------|
| Frontend | Requests | CDN, caching |
| Backend | CPU | Horizontal scaling |
| Database | Connections | Connection pooling |
| ImageMagick | CPU/Memory | Worker scaling |
| Storage | I/O | SSD, object storage |

---

## Next Steps

- [[Deployment]] - Production setup
- [[Performance]] - Optimization tips
- [[Security]] - Security best practices
