# Installation Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Option 1: Pre-built Image](#option-1-pre-built-image-recommended)
- [Option 2: Build from Source](#option-2-build-from-source)
- [Changing Ports](#changing-ports)
- [Configuration](#configuration)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [Production Deployment](#production-deployment)

---

## Quick Start

The fastest way to get started:
```bash
mkdir imagemagick-webgui && cd imagemagick-webgui
curl -O https://raw.githubusercontent.com/PrzemekSkw/imagemagick-webui/main/docker-compose.example.yml
mv docker-compose.example.yml docker-compose.yml
docker compose up -d
```

Access: http://localhost:3000

---

## Option 1: Pre-built Image (Recommended)

**Best for:** Production use, quick testing, no development

**Steps:**
```bash
mkdir imagemagick-webgui && cd imagemagick-webgui
curl -O https://raw.githubusercontent.com/PrzemekSkw/imagemagick-webui/main/docker-compose.example.yml
mv docker-compose.example.yml docker-compose.yml
docker compose up -d
```

**Advantages:**
- ✅ No build time (starts in ~30 seconds)
- ✅ Smaller download
- ✅ Production-ready

**Default configuration:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- No authentication required
- 100MB max upload

---

## Option 2: Build from Source

**Best for:** Development, customization, contributing

**Steps:**
```bash
git clone https://github.com/PrzemekSkw/imagemagick-webui.git
cd imagemagick-webgui
cp .env.example .env
nano .env  # Optional: customize settings
docker compose up -d
```

**Advantages:**
- ✅ Full source code
- ✅ Easy customization
- ✅ Can contribute changes

**Build time:** ~5-10 minutes (first time)

---

## Changing Ports

### If using Option 1 (pre-built image):

**Edit `docker-compose.yml`:**

Find and change these lines:
```yaml
    args:
        NEXT_PUBLIC_API_PORT: "8012"  # ← Change to match backend port
    ports:
      - "3012:3000"  # ← Change "3012" to your desired frontend port
      - "8012:8000"  # ← Change "8012" to your desired backend port
    environment:
      - NEXT_PUBLIC_API_PORT=8012  # ← MUST match backend port above
```

**Then restart:**
```bash
docker compose down
docker compose up -d
```

**Note:** No rebuild needed when using pre-built image!

---

### If using Option 2 (built from source):

**Edit `.env`:**
```env
FRONTEND_PORT=3012
BACKEND_PORT=8012
NEXT_PUBLIC_API_PORT=8012  # Must match BACKEND_PORT
```

**Then rebuild:**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

**Why rebuild?** The `NEXT_PUBLIC_API_PORT` is baked into the frontend at build time.

---

## Configuration

### Authentication

**Enable login requirement:**
```yaml
# In docker-compose.yml:
environment:
  - REQUIRE_LOGIN=true
  - ALLOW_REGISTRATION=false  # Disable new signups after creating admin
```

Restart: `docker compose restart`

---

### Image Processing Settings
```yaml
environment:
  - DEFAULT_OUTPUT_FORMAT=avif     # avif, webp, jpeg, png
  - DEFAULT_QUALITY=90             # 1-100
  - MAX_UPLOAD_SIZE_MB=200         # Maximum file size
  - IMAGEMAGICK_TIMEOUT=600        # Processing timeout (seconds)
```

---

### Security Keys (PRODUCTION REQUIRED!)

**Generate secure keys:**
```bash
# Linux/Mac:
openssl rand -hex 32

# Or Python:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Update docker-compose.yml:**
```yaml
environment:
  - SECRET_KEY=your-generated-key-here
  - JWT_SECRET=your-other-generated-key-here
```

---

## Reverse Proxy Setup

### Nginx Proxy Manager

**Proxy Host - Details:**
```
Domain Names: example.com
Scheme: http
Forward Hostname/IP: YOUR_SERVER_IP
Forward Port: 3000

☑ Websockets Support
☐ Cache Assets
```

**Custom Locations - Add `/api`:**
```
Location: /api
Scheme: http
Forward Hostname/IP: YOUR_SERVER_IP
Forward Port: 8000

Custom Nginx Configuration:
client_max_body_size 100M;
proxy_connect_timeout 300;
proxy_send_timeout 300;
proxy_read_timeout 300;
```

**SSL:**
```
☑ Force SSL
☑ HTTP/2 Support
☑ Request SSL Certificate
```

**Update CORS:**
```yaml
# In docker-compose.yml:
environment:
  - ALLOWED_ORIGINS=https://example.com
```

Restart: `docker compose restart`

---

### Traefik

Add labels to docker-compose.yml:
```yaml
services:
  app:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.imagemagick.rule=Host(`example.com`)"
      - "traefik.http.routers.imagemagick.entrypoints=websecure"
      - "traefik.http.routers.imagemagick.tls.certresolver=myresolver"
      - "traefik.http.services.imagemagick.loadbalancer.server.port=3000"
```

---

### Caddy

Create `Caddyfile`:
```
example.com {
    reverse_proxy localhost:3000
    
    @api path /api/*
    handle @api {
        reverse_proxy localhost:8000
    }
}
```

---

## Production Deployment

### Pre-deployment Checklist

- [ ] Change `SECRET_KEY` to random 32+ character string
- [ ] Change `JWT_SECRET` to random 32+ character string  
- [ ] Set `REQUIRE_LOGIN=true`
- [ ] Set `ALLOW_REGISTRATION=false` after creating admin
- [ ] Configure `ALLOWED_ORIGINS` with your domain
- [ ] Set up HTTPS via reverse proxy
- [ ] Configure backups for Docker volumes
- [ ] Test upload/download functionality
- [ ] Monitor resource usage

---

### Backups

**Backup volumes:**
```bash
docker run --rm \
  -v imagemagick-webgui_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup-$(date +%Y%m%d).tar.gz -C /data .
```

**Restore:**
```bash
docker run --rm \
  -v imagemagick-webgui_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup-20241215.tar.gz -C /data
```

---

### Updates

**Option 1 (pre-built image):**
```bash
docker compose pull
docker compose up -d
```

**Option 2 (built from source):**
```bash
git pull
docker compose build --no-cache
docker compose up -d
```

---

## Troubleshooting

### Port already in use
```bash
# Check what's using the port:
sudo lsof -i :3000
sudo lsof -i :8000

# Change ports in docker-compose.yml
```

### Upload fails
```bash
# Check logs:
docker compose logs app | grep -i error

# Increase upload size:
# Edit docker-compose.yml:
environment:
  - MAX_UPLOAD_SIZE_MB=500
```

### Can't connect from other devices
```bash
# Check ALLOWED_ORIGINS:
environment:
  - ALLOWED_ORIGINS=*  # Allow all (testing only!)
  # Or specific:
  - ALLOWED_ORIGINS=https://example.com,http://192.168.1.100:3000
```

---

## Support

- 🐛 [Report Issues](https://github.com/PrzemekSkw/imagemagick-webui/issues)
- 💬 [Discussions](https://github.com/PrzemekSkw/imagemagick-webui/discussions)
- 📖 [Documentation](https://github.com/PrzemekSkw/imagemagick-webui/wiki)
