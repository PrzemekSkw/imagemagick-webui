# Installation

## Prerequisites

Before installing ImageMagick WebGUI, ensure you have:

- **Docker** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ ([Install Compose](https://docs.docker.com/compose/install/))

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2 GB | 4 GB (8 GB for AI features) |
| CPU | 2 cores | 4 cores |
| Disk | 5 GB | 10 GB |
| Architecture | x86_64 (AMD/Intel) | x86_64 |

> ⚠️ ARM architecture (Raspberry Pi, Apple Silicon) is not fully supported due to onnxruntime limitations.

---

## Quick Install (Recommended)

The easiest way to run ImageMagick WebGUI using the pre-built Docker image:
```bash
# Create directory
mkdir imagemagick-webgui && cd imagemagick-webgui

# Download docker-compose file
curl -O https://raw.githubusercontent.com/PrzemekSkw/imagemagick-webui/main/docker-compose.example.yml
mv docker-compose.example.yml docker-compose.yml

# Start the application
docker compose up -d
```

**That's it!** Open http://localhost:3000

---

## Build from Source

If you want to modify the code or build locally:
```bash
# Clone repository
git clone https://github.com/PrzemekSkw/imagemagick-webui.git
cd imagemagick-webgui

# Copy environment file
cp .env.example .env

# Build and start (takes 5-10 minutes first time)
docker compose up --build -d
```

---

## Custom Ports

If ports 3000 or 8000 are already in use, edit `docker-compose.yml`:
```yaml
services:
  app:
    ports:
      - "3016:3000"   # Frontend on port 3016
      - "8016:8000"   # Backend on port 8016
```

---

## Access from Phone/Tablet

The application automatically detects your IP address. To access from other devices on the same network:

1. Find your computer's IP:
```bash
   # Linux/Mac
   ip addr | grep "inet 192"
   
   # Windows
   ipconfig
```

2. Open on phone: `http://192.168.x.x:3000`

---

## Updating

To update to the latest version:
```bash
docker compose pull
docker compose up -d
```

---

## Uninstalling

To completely remove the application:
```bash
# Stop and remove containers
docker compose down

# Remove volumes (deletes all data!)
docker compose down -v

# Remove images
docker rmi ghcr.io/przemekskw/imagemagick-webui:latest
```

---

## Local Development (without Docker)

For development:

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL and Redis via Docker:
docker run -d --name postgres -e POSTGRES_PASSWORD=imagemagick -p 5432:5432 postgres:16-alpine
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Run backend
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Troubleshooting

### Container won't start
Check logs:
```bash
docker compose logs app
```

### Database connection error
Wait 30 seconds and try again - PostgreSQL needs time to initialize on first run.

### Permission denied errors
On Linux, you may need:
```bash
sudo docker compose up -d
```

### Out of memory
Reduce ImageMagick memory limit in docker-compose.yml:
```yaml
environment:
  - IMAGEMAGICK_MEMORY_LIMIT=1GiB
```

See [Troubleshooting](Troubleshooting) for more solutions.
