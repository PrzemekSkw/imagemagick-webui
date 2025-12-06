# Performance

Optimization tips and performance tuning for ImageMagick WebGUI.

---

## Performance Overview

### Typical Processing Times

| Operation | 1080p Image | 4K Image |
|-----------|-------------|----------|
| Resize | 0.2-0.5s | 0.5-1s |
| Crop | 0.1-0.3s | 0.3-0.5s |
| Blur (10px) | 0.5-1s | 2-4s |
| Sharpen | 0.3-0.5s | 0.5-1s |
| Watermark | 0.2-0.4s | 0.4-0.8s |
| Format Convert | 0.3-0.8s | 0.8-2s |
| AI Background Removal | 15-30s | 45-90s |
| AI Upscale 2x | 2-5s | 10-20s |

---

## Optimization Strategies

### 1. Image Size Reduction

**Before processing, resize large images:**

```bash
# Resize images larger than 4K before other operations
-resize "4096x4096>"
```

**Impact:**
| Original | After Resize | Speed Improvement |
|----------|--------------|-------------------|
| 8K (7680×4320) | 4K (3840×2160) | 4x faster |
| 4K (3840×2160) | 1080p (1920×1080) | 4x faster |

### 2. Output Format

**WebP is fastest:**

| Format | Encode Speed | File Size |
|--------|--------------|-----------|
| WebP | Fast | Small |
| JPEG | Fast | Medium |
| PNG | Slow | Large |
| AVIF | Very Slow | Smallest |

### 3. Quality Settings

**Lower quality = faster encoding:**

| Quality | Speed | Use Case |
|---------|-------|----------|
| 60-70% | Fastest | Thumbnails |
| 80-85% | Fast | Web standard |
| 90-95% | Moderate | High quality |
| 100% | Slow | Archival |

---

## Server Optimization

### Memory Settings

**docker-compose.yml:**
```yaml
services:
  app:
    environment:
      - IMAGEMAGICK_MEMORY_LIMIT=2GB
    deploy:
      resources:
        limits:
          memory: 4G
```

### CPU Allocation

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
```

### Worker Scaling

**More workers for parallel processing:**
```yaml
services:
  worker:
    deploy:
      replicas: 4
```

---

## ImageMagick Tuning

### Policy.xml

Create `/etc/ImageMagick-7/policy.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<policymap>
  <policy domain="resource" name="memory" value="2GiB"/>
  <policy domain="resource" name="map" value="4GiB"/>
  <policy domain="resource" name="width" value="16KP"/>
  <policy domain="resource" name="height" value="16KP"/>
  <policy domain="resource" name="area" value="128MP"/>
  <policy domain="resource" name="disk" value="4GiB"/>
  <policy domain="resource" name="thread" value="4"/>
  <policy domain="resource" name="time" value="120"/>
</policymap>
```

### Parallel Processing

```bash
# Use multiple threads
-limit thread 4
```

### Disk Cache

```bash
# Use disk for large images
-limit memory 512MiB
-limit map 1GiB
```

---

## Database Optimization

### Connection Pooling

**config.py:**
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
```

### Indexes

```sql
-- Add indexes for common queries
CREATE INDEX idx_images_user_id ON images(user_id);
CREATE INDEX idx_images_created_at ON images(created_at DESC);
CREATE INDEX idx_jobs_status ON jobs(status);
```

### Vacuum

```bash
# Regular maintenance
docker compose exec db psql -U imagemagick -c "VACUUM ANALYZE;"
```

---

## Redis Optimization

### Memory Settings

**redis.conf:**
```
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### Connection

```python
REDIS_URL=redis://redis:6379/0?socket_timeout=5&socket_connect_timeout=5
```

---

## Frontend Optimization

### Image Lazy Loading

```tsx
<img loading="lazy" src={thumbnail} />
```

### Thumbnail Sizes

| Use Case | Size | Format |
|----------|------|--------|
| Gallery grid | 300×300 | WebP |
| Preview | 800×800 | WebP |
| Full view | Original | Original |

### Caching

**next.config.js:**
```javascript
module.exports = {
  images: {
    minimumCacheTTL: 3600,
  },
};
```

---

## Batch Processing Tips

### Optimal Batch Sizes

| Images | Recommended |
|--------|-------------|
| 1-10 | Process immediately |
| 10-50 | Queue recommended |
| 50-100 | Split into chunks |
| 100+ | Process in batches of 50 |

### Memory Management

```python
# Process in chunks to avoid memory issues
for chunk in chunks(images, 10):
    process_batch(chunk)
    gc.collect()  # Force garbage collection
```

---

## Monitoring Performance

### Response Time

```bash
# Check API response time
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8000/health
```

### Processing Time

```bash
# Check logs for processing duration
docker compose logs app | grep "Processing time"
```

### Resource Usage

```bash
# Real-time monitoring
docker stats

# Detailed memory
docker compose exec app ps aux --sort=-%mem
```

---

## Common Bottlenecks

### CPU-Bound Operations

| Operation | CPU Impact |
|-----------|------------|
| Blur (large radius) | High |
| Sharpen | Medium |
| AI Background Removal | Very High |
| Format conversion | Medium |

**Solution:** Scale workers, limit concurrent jobs

### Memory-Bound Operations

| Operation | Memory Impact |
|-----------|---------------|
| Large image resize | High |
| AI operations | Very High |
| Multiple concurrent jobs | Cumulative |

**Solution:** Limit image size, reduce concurrency

### I/O-Bound Operations

| Operation | I/O Impact |
|-----------|------------|
| Upload | High |
| Download | High |
| Disk cache | Medium |

**Solution:** Use SSD, increase buffer sizes

---

## Benchmarks

### Test Setup

```bash
# Create test images
for i in {1..100}; do
    convert -size 1920x1080 xc:red test_$i.jpg
done
```

### Run Benchmark

```bash
# Time batch operation
time curl -X POST http://localhost:8000/api/operations/process \
    -H "Content-Type: application/json" \
    -d '{"image_ids": [1,2,3,...], "operations": [{"operation": "resize", "params": {"percent": 50}}]}'
```

### Expected Results

| Configuration | 100 Images | Time |
|---------------|------------|------|
| 1 worker, 2GB | Sequential | ~120s |
| 4 workers, 4GB | Parallel | ~35s |
| 4 workers, 8GB | Parallel | ~30s |

---

## Best Practices

1. **Resize early** - Reduce before other operations
2. **Use WebP** - Best compression/speed ratio
3. **Limit concurrency** - Prevent memory exhaustion
4. **Monitor resources** - Watch for bottlenecks
5. **Scale workers** - Parallel processing helps
6. **Cache thumbnails** - Don't regenerate
7. **Clean temp files** - Free disk space regularly

---

## Next Steps

- [[Deployment]] - Production setup
- [[Architecture]] - System design
- [[Troubleshooting]] - Common issues
