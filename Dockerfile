# ============================================
# STAGE 1: Frontend Builder
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Set API URL for build time (will be accessed from browser)
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

# Install dependencies
COPY frontend/package.json ./
RUN npm install --legacy-peer-deps

# Copy source and build
COPY frontend/ ./
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# ============================================
# STAGE 2: Python Dependencies
# IMPORTANT: Pin to Python 3.12 - onnxruntime doesn't support 3.13+ yet
# ============================================
FROM python:3.14.1-slim AS python-deps

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 3: Final Production Image
# IMPORTANT: Must match Python version from stage 2
# ============================================
FROM python:3.14.1-slim AS production

LABEL maintainer="ImageMagick WebGUI"
LABEL description="Production-ready ImageMagick WebGUI application"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    NODE_ENV=production \
    NUMBA_CACHE_DIR=/tmp/numba_cache \
    NUMBA_DISABLE_JIT=1 \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app

# Install runtime dependencies + ImageMagick + Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick \
    libmagickwand-dev \
    ghostscript \
    poppler-utils \
    libpq5 \
    libmagic1 \
    curl \
    tini \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configure ImageMagick policy for PDF support and security
RUN POLICY_FILE=$(find /etc -name "policy.xml" -path "*ImageMagick*" 2>/dev/null | head -1) && \
    if [ -n "$POLICY_FILE" ] && [ -f "$POLICY_FILE" ]; then \
    echo "Found policy file: $POLICY_FILE"; \
    sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' "$POLICY_FILE"; \
    sed -i 's/rights="none" pattern="PS"/rights="read|write" pattern="PS"/' "$POLICY_FILE"; \
    sed -i 's/rights="none" pattern="EPS"/rights="read|write" pattern="EPS"/' "$POLICY_FILE"; \
    sed -i 's/<policy domain="resource" name="memory" value="[^"]*"\/>/<policy domain="resource" name="memory" value="2GiB"\/>/' "$POLICY_FILE"; \
    sed -i 's/<policy domain="resource" name="disk" value="[^"]*"\/>/<policy domain="resource" name="disk" value="4GiB"\/>/' "$POLICY_FILE"; \
    sed -i 's/<policy domain="resource" name="width" value="[^"]*"\/>/<policy domain="resource" name="width" value="16KP"\/>/' "$POLICY_FILE"; \
    sed -i 's/<policy domain="resource" name="height" value="[^"]*"\/>/<policy domain="resource" name="height" value="16KP"\/>/' "$POLICY_FILE"; \
    fi

# Verify ImageMagick installation
RUN convert -version && identify -version

# Copy Python virtual environment
COPY --from=python-deps /opt/venv /opt/venv

# Copy built frontend (standalone mode)
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend/.next/standalone
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/standalone/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend/.next/standalone/public

# Copy backend source
COPY backend/ ./backend/

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Create directories with proper permissions
RUN mkdir -p /app/uploads /app/processed /tmp/imagemagick /tmp/numba_cache /tmp/matplotlib /home/appuser/.u2net && \
    chown -R appuser:appuser /app /tmp/imagemagick /tmp/numba_cache /tmp/matplotlib /home/appuser

# Set HOME and U2NET paths
ENV HOME=/home/appuser \
    U2NET_HOME=/home/appuser/.u2net

# Pre-download rembg model (as root, then fix permissions)
RUN python -c "from rembg import new_session; new_session('u2net')" || echo "Model download failed, will retry at runtime"
RUN chown -R appuser:appuser /home/appuser/.u2net || true

# Copy startup script
COPY scripts/start.sh /start.sh
RUN chmod +x /start.sh

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 3000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/api/health && curl -f http://localhost:8000/health || exit 1

# Use tini as init
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start both services
CMD ["/start.sh"]
