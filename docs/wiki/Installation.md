# Installation

## Prerequisites

Before installing ImageMagick WebGUI, ensure you have:

- **Docker** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ ([Install Compose](https://docs.docker.com/compose/install/))
- **Git** (optional, for cloning)

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2 GB | 4 GB |
| CPU | 2 cores | 4 cores |
| Disk | 5 GB | 10 GB |
| OS | Linux, macOS, Windows 10+ | Linux |

---

## Installation Methods

### Method 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/przemekskw/imagemagick-webui.git
cd imagemagick-webui

# Start all services
docker compose up --build
```

The first build takes 5-10 minutes. Subsequent starts are instant.

### Method 2: Download Release

1. Go to [Releases](https://github.com/przemekskw/imagemagick-webui/releases)
2. Download the latest `imagemagick-webgui.zip`
3. Extract and run:

```bash
unzip imagemagick-webgui.zip
cd imagemagick-webgui
docker compose up --build
```

### Method 3: Local Development

For development without Docker:

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL and Redis locally or via Docker:
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

## Verify Installation

After starting, verify all services are running:

```bash
docker compose ps
```

Expected output:
```
NAME                    STATUS
imagemagick-webgui-app  running (healthy)
imagemagick-webgui-db   running
imagemagick-webgui-redis running
imagemagick-webgui-worker running
```

### Access Points

| Service | URL |
|---------|-----|
| Web Interface | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## Troubleshooting Installation

### Port Already in Use

```bash
# Check what's using port 3000
lsof -i :3000  # Linux/macOS
netstat -ano | findstr :3000  # Windows

# Change ports in docker-compose.yml
ports:
  - "3001:3000"  # Use 3001 instead
```

### Docker Build Fails

```bash
# Clean Docker cache
docker compose down -v
docker system prune -af
docker compose build --no-cache
```

### Permission Denied

```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Out of Memory

```bash
# Increase Docker memory limit
# Docker Desktop: Settings → Resources → Memory → 4GB+
```

---

## Next Steps

- [[Configuration]] - Customize your installation
- [[Quick Start Guide]] - Process your first image
- [[Dashboard Overview]] - Learn the interface
