# Security

Security considerations and best practices for ImageMagick WebGUI.

---

## Security Overview

ImageMagick WebGUI implements multiple security layers:

```
┌─────────────────────────────────────┐
│         HTTPS/TLS                   │
├─────────────────────────────────────┤
│         Rate Limiting               │
├─────────────────────────────────────┤
│         Authentication (JWT)        │
├─────────────────────────────────────┤
│         Input Validation            │
├─────────────────────────────────────┤
│         Path Traversal Protection   │
├─────────────────────────────────────┤
│         Command Whitelist           │
├─────────────────────────────────────┤
│         Resource Limits             │
├─────────────────────────────────────┤
│         Non-root Container          │
└─────────────────────────────────────┘
```

---

## Authentication Security

### Password Storage

- **Algorithm:** bcrypt
- **Salt rounds:** 12
- **Never stored in plain text**

### JWT Tokens

- **Algorithm:** HS256
- **Expiration:** Configurable (default 60 min)
- **Storage:** httpOnly cookies
- **Secret key:** Must be changed in production

### Best Practices

1. **Strong SECRET_KEY:**
   ```bash
   openssl rand -hex 32
   ```

2. **Short token expiry:**
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. **HTTPS only:**
   - Tokens encrypted in transit
   - Prevents MITM attacks

---

## Input Validation

### File Upload Validation

| Check | Description |
|-------|-------------|
| MIME type | Verify actual file type |
| Extension | Match against whitelist |
| File size | Max 50MB (configurable) |
| Magic bytes | Validate file signature |

**Allowed formats:**
```python
ALLOWED_EXTENSIONS = [
    "jpg", "jpeg", "png", "gif", "webp",
    "tiff", "pdf", "svg", "avif", "bmp"
]
```

### API Input Validation

All inputs validated with Pydantic:

```python
class ProcessRequest(BaseModel):
    image_id: int = Field(..., gt=0)
    operations: List[Operation]
    output_format: str = Field(..., regex="^(jpg|png|webp|gif)$")
    quality: int = Field(default=85, ge=1, le=100)
```

---

## Path Traversal Protection

### Validation Function

```python
ALLOWED_DIRS = [
    "/app/uploads",
    "/app/processed",
    "/tmp"
]

def validate_path(file_path: str) -> str:
    abs_path = os.path.realpath(file_path)
    
    is_allowed = any(
        abs_path.startswith(allowed_dir)
        for allowed_dir in ALLOWED_DIRS
    )
    
    if not is_allowed:
        raise HTTPException(403, "Access denied")
    
    return abs_path
```

### Blocked Patterns

- `../` - Parent directory
- Absolute paths outside allowed dirs
- Symbolic links to restricted areas

---

## Command Injection Protection

### Whitelist Approach

Only allowed ImageMagick operations:

```python
ALLOWED_OPERATIONS = [
    "resize", "crop", "rotate", "flip", "flop",
    "blur", "sharpen", "brightness-contrast",
    "colorspace", "modulate", "sepia-tone",
    "grayscale", "negate", "quality", "strip",
    "annotate", "gravity", "pointsize", "fill"
]
```

### Safe Execution

```python
# Using subprocess with list (not shell)
process = await asyncio.create_subprocess_exec(
    *command_list,  # Not shell=True
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)
```

### Blocked Operations

- Shell commands (`rm`, `wget`, `curl`)
- File system access (`-write`, `-read`)
- Network operations
- Script execution

---

## Resource Limits

### ImageMagick Limits

```env
IMAGEMAGICK_TIMEOUT=60        # 60 seconds max
IMAGEMAGICK_MEMORY_LIMIT=2GB  # 2GB RAM max
IMAGEMAGICK_DISK_LIMIT=4GB    # 4GB temp disk
```

### Docker Limits

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Purpose

Prevents:
- Denial of Service (DoS)
- Memory exhaustion
- CPU exhaustion
- Disk space exhaustion

---

## Rate Limiting

### Limits

| Endpoint | Limit |
|----------|-------|
| Login | 5/minute |
| Register | 3/minute |
| Upload | 10/minute |
| Process | 20/minute |
| API (general) | 100/minute |

### Implementation

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

## Container Security

### Non-root User

```dockerfile
# Create non-root user
RUN useradd -m -s /bin/bash appuser

# Switch to non-root
USER appuser
```

### Read-only Filesystem

```yaml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
```

### Security Options

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
```

---

## Network Security

### Firewall Rules

```bash
# Allow only HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Internal Network

```yaml
networks:
  internal:
    internal: true  # No external access
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## Sensitive Data Protection

### Environment Variables

```bash
# Never commit secrets
echo ".env" >> .gitignore

# Use strong secrets
SECRET_KEY=$(openssl rand -hex 32)
```

### Logging

```python
# Never log sensitive data
logger.info(f"Login attempt for user: {email}")  # OK
logger.info(f"Password: {password}")  # NEVER!
```

### Database

```python
# Encrypt sensitive fields
encrypted_secret = encrypt(totp_secret)
```

---

## Security Headers

### Nginx

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self';" always;
```

### FastAPI

```python
from starlette.middleware import Middleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI(middleware=[
    Middleware(HTTPSRedirectMiddleware)
])
```

---

## Security Checklist

### Before Deployment

- [ ] Changed `SECRET_KEY`
- [ ] Strong database password
- [ ] HTTPS configured
- [ ] Rate limiting enabled
- [ ] Firewall configured
- [ ] Non-root container user
- [ ] Resource limits set
- [ ] Logging configured
- [ ] Backups scheduled

### Ongoing

- [ ] Regular updates
- [ ] Log monitoring
- [ ] Security scanning
- [ ] Dependency updates
- [ ] Backup testing

---

## Vulnerability Reporting

If you discover a security vulnerability:

1. **Do not** open a public issue
2. Email: security@yourdomain.com
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
4. Allow 90 days for fix before disclosure

---

## Known Limitations

1. **No 2FA** - Single factor authentication only
2. **No IP whitelisting** - Accept all IPs
3. **Session storage** - Stateless JWT (can't revoke)
4. **Audit logging** - Basic logging only

---

## Updates & Patches

### Monitoring

```bash
# Check for updates
docker compose pull

# Check dependencies
pip list --outdated
npm outdated
```

### Applying Updates

```bash
git pull
docker compose down
docker compose up -d --build
```

---

## Next Steps

- [[Deployment]] - Secure deployment
- [[Configuration]] - Security settings
- [[Architecture]] - Security architecture
