# Configuration

ImageMagick WebGUI can be configured through environment variables.

## Environment Variables

Create a `.env` file in the project root:

```env
# ===================
# Database
# ===================
DATABASE_URL=postgresql+asyncpg://imagemagick:imagemagick@db:5432/imagemagick

# ===================
# Security
# ===================
# IMPORTANT: Change this in production!
SECRET_KEY=your-super-secret-key-change-me-in-production

# JWT token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ===================
# ImageMagick Limits
# ===================
# Maximum processing time (seconds)
IMAGEMAGICK_TIMEOUT=60

# Memory limit per operation
IMAGEMAGICK_MEMORY_LIMIT=2GB

# Disk space limit
IMAGEMAGICK_DISK_LIMIT=4GB

# ===================
# Upload Settings
# ===================
# Maximum file size
MAX_UPLOAD_SIZE=50MB

# Allowed file extensions
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,webp,tiff,pdf,svg,avif

# ===================
# Storage
# ===================
# Upload directory
UPLOAD_DIR=/app/uploads

# Processed files directory
OUTPUT_DIR=/app/processed

# Temporary files
TEMP_DIR=/tmp/imagemagick

# ===================
# Queue Settings
# ===================
# Redis connection
REDIS_URL=redis://redis:6379/0

# Maximum concurrent jobs
MAX_CONCURRENT_JOBS=5

# Job timeout (seconds)
JOB_TIMEOUT=300

# ===================
# Optional: Google OAuth
# ===================
# GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=your-client-secret

# ===================
# Optional: Frontend
# ===================
# API URL (for frontend to reach backend)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Configuration Sections

### Database

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

| Part | Description |
|------|-------------|
| `postgresql+asyncpg` | Database driver |
| `user:pass` | Credentials |
| `host:5432` | Database server |
| `dbname` | Database name |

### Security Settings

```env
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Important:** Always change `SECRET_KEY` in production!

Generate a secure key:
```bash
openssl rand -hex 32
# or
python -c "import secrets; print(secrets.token_hex(32))"
```

### ImageMagick Limits

These limits protect your server from resource exhaustion:

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGEMAGICK_TIMEOUT` | 60 | Max seconds per operation |
| `IMAGEMAGICK_MEMORY_LIMIT` | 2GB | RAM limit per operation |
| `IMAGEMAGICK_DISK_LIMIT` | 4GB | Temp disk usage limit |

### Upload Settings

```env
MAX_UPLOAD_SIZE=50MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,webp,tiff,pdf,svg,avif
```

### Queue Settings

```env
REDIS_URL=redis://redis:6379/0
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT=300
```

---

## Docker Compose Override

For advanced configuration, create `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  app:
    environment:
      - SECRET_KEY=my-production-secret
      - MAX_UPLOAD_SIZE=100MB
    ports:
      - "8080:3000"  # Change frontend port
    volumes:
      - ./my-uploads:/app/uploads  # Custom upload directory
    
  db:
    environment:
      - POSTGRES_PASSWORD=secure-password
    volumes:
      - ./data/postgres:/var/lib/postgresql/data  # Persist data
```

---

## Production Configuration

### Recommended Production Settings

```env
# Strong secret key
SECRET_KEY=<generated-64-char-hex>

# Shorter token expiry
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Conservative limits
IMAGEMAGICK_TIMEOUT=30
IMAGEMAGICK_MEMORY_LIMIT=1GB
MAX_UPLOAD_SIZE=25MB

# Disable debug
DEBUG=false
```

### Security Checklist

- [ ] Changed `SECRET_KEY`
- [ ] Set strong database password
- [ ] Configured HTTPS (reverse proxy)
- [ ] Set up firewall rules
- [ ] Enabled rate limiting
- [ ] Configured backup for database

---

## Settings UI

Some settings can also be changed in the web interface:

1. Go to **Settings** (gear icon)
2. Configure:
   - Theme (Dark/Light/Auto)
   - Default output format
   - Default quality
   - Max concurrent jobs
   - Auto-delete originals

These settings are stored per-user in the database.

---

## Next Steps

- [[Quick Start Guide]] - Start processing images
- [[Security]] - Security best practices
- [[Deployment]] - Production deployment
