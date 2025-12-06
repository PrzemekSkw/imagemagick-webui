# Deployment

Production deployment guide for ImageMagick WebGUI.

---

## Deployment Options

| Method | Complexity | Best For |
|--------|------------|----------|
| Docker Compose | Easy | Single server |
| Kubernetes | Complex | Large scale |
| Cloud Run | Medium | Serverless |
| VPS | Easy | Personal use |

---

## Docker Compose (Recommended)

### Prerequisites

- Linux server (Ubuntu 22.04+ recommended)
- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ RAM
- 10GB+ disk space

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Logout and login to apply group changes
```

### Step 2: Clone Repository

```bash
git clone https://github.com/przemekskw/imagemagick-webui.git
cd imagemagick-webui
```

### Step 3: Configure Environment

```bash
cp .env.example .env
nano .env
```

**Production .env:**
```env
# Security - CHANGE THESE!
SECRET_KEY=your-64-char-random-string-here
DATABASE_URL=postgresql+asyncpg://imagemagick:secure_password@db:5432/imagemagick

# ImageMagick
IMAGEMAGICK_TIMEOUT=60
IMAGEMAGICK_MEMORY_LIMIT=2GB

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

Generate secure key:
```bash
openssl rand -hex 32
```

### Step 4: Start Services

```bash
docker compose up -d --build
```

### Step 5: Verify

```bash
# Check services
docker compose ps

# Check logs
docker compose logs -f

# Test health
curl http://localhost:8000/health
```

---

## Reverse Proxy Setup

### Nginx

```nginx
# /etc/nginx/sites-available/imagemagick-webui
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/imagemagick-webui /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Caddy (Simpler)

```caddyfile
# /etc/caddy/Caddyfile
yourdomain.com {
    reverse_proxy localhost:3000
    
    handle /api/* {
        reverse_proxy localhost:8000
    }
    
    encode gzip
}
```

### Traefik (Docker-native)

```yaml
# docker-compose.override.yml
services:
  app:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.imagemagick.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.imagemagick.tls.certresolver=letsencrypt"
```

---

## SSL/TLS Certificates

### Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

---

## Systemd Service

For auto-start on boot:

```ini
# /etc/systemd/system/imagemagick-webui.service
[Unit]
Description=ImageMagick WebGUI
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/imagemagick-webui
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=root

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl enable imagemagick-webui
sudo systemctl start imagemagick-webui
```

---

## Backup Strategy

### Database Backup

```bash
# Manual backup
docker compose exec db pg_dump -U imagemagick imagemagick > backup.sql

# Restore
cat backup.sql | docker compose exec -T db psql -U imagemagick imagemagick
```

### Automated Backups

```bash
# /opt/scripts/backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/opt/backups

# Database
docker compose -f /opt/imagemagick-webui/docker-compose.yml \
    exec -T db pg_dump -U imagemagick imagemagick \
    > $BACKUP_DIR/db_$DATE.sql

# Uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/imagemagick-webui/uploads

# Keep last 7 days
find $BACKUP_DIR -mtime +7 -delete
```

Cron job:
```bash
# crontab -e
0 2 * * * /opt/scripts/backup.sh
```

---

## Monitoring

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "imagemagick": "7.1.1-21"
}
```

### Docker Stats

```bash
docker stats imagemagick-webui-app-1
```

### Log Monitoring

```bash
# Follow logs
docker compose logs -f

# Specific service
docker compose logs -f app

# Last 100 lines
docker compose logs --tail 100
```

---

## Updating

### Standard Update

```bash
cd /opt/imagemagick-webui

# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose up -d --build

# Verify
docker compose ps
curl http://localhost:8000/health
```

### With Backup

```bash
# Backup first
./backup.sh

# Then update
git pull
docker compose down
docker compose up -d --build
```

---

## Scaling

### Horizontal Scaling (Workers)

```yaml
# docker-compose.override.yml
services:
  worker:
    deploy:
      replicas: 3
```

### Resource Limits

```yaml
# docker-compose.override.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
```

---

## Security Checklist

- [ ] Changed default `SECRET_KEY`
- [ ] Strong database password
- [ ] HTTPS enabled
- [ ] Firewall configured (only 80, 443 open)
- [ ] Regular backups enabled
- [ ] Monitoring configured
- [ ] Log rotation enabled
- [ ] Rate limiting configured
- [ ] Non-root user in Docker

---

## Troubleshooting

### Container Won't Start

```bash
docker compose logs app
docker compose ps
```

### Database Connection Failed

```bash
# Check database status
docker compose exec db pg_isready

# Check connection
docker compose exec app python -c "from app.core.database import engine; print('OK')"
```

### Out of Disk Space

```bash
# Clean Docker
docker system prune -af

# Clean old images
docker image prune -af
```

### Memory Issues

```bash
# Check memory usage
free -h
docker stats

# Increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Next Steps

- [[Performance]] - Optimization tips
- [[Security]] - Security hardening
- [[Architecture]] - System design
