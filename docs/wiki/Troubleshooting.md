# Troubleshooting

Common issues and solutions for ImageMagick WebGUI.

---

## 🚀 Startup Issues

### Container Won't Start

**Symptoms:** `docker compose up` fails or container exits immediately.

**Solutions:**

1. **Check logs:**
   ```bash
   docker compose logs app
   docker compose logs db
   ```

2. **Port conflicts:**
   ```bash
   # Check if ports are in use
   lsof -i :3000
   lsof -i :8000
   
   # Change ports in docker-compose.yml
   ports:
     - "3001:3000"
   ```

3. **Clean restart:**
   ```bash
   docker compose down -v
   docker system prune -af
   docker compose up --build
   ```

### Database Connection Failed

**Error:** `connection refused` or `database does not exist`

**Solutions:**

1. Wait for database to initialize (first run takes ~30s)
2. Check database logs: `docker compose logs db`
3. Verify DATABASE_URL in .env
4. Reset database:
   ```bash
   docker compose down -v
   docker compose up
   ```

### Health Check Failing

**Error:** Container shows `unhealthy`

**Solutions:**

1. Check both services:
   ```bash
   curl http://localhost:3000/api/health
   curl http://localhost:8000/health
   ```

2. Increase start period in docker-compose.yml:
   ```yaml
   healthcheck:
     start_period: 120s
   ```

---

## 📤 Upload Issues

### File Too Large

**Error:** `413 Request Entity Too Large`

**Solutions:**

1. Check MAX_UPLOAD_SIZE in .env (default: 50MB)
2. For larger files, increase limit:
   ```env
   MAX_UPLOAD_SIZE=100MB
   ```

### Unsupported Format

**Error:** `Unsupported file type`

**Solutions:**

1. Check ALLOWED_EXTENSIONS in .env
2. Verify file is actually the claimed format
3. Try converting to PNG/JPG first

### Upload Stuck

**Symptoms:** Progress bar stuck, no response

**Solutions:**

1. Check network connection
2. Check backend logs: `docker compose logs app`
3. Reduce file size or try different file
4. Clear browser cache

---

## 🖼️ Processing Issues

### Operation Failed

**Error:** `Command failed` or `Processing error`

**Solutions:**

1. Check backend logs for specific error:
   ```bash
   docker compose logs app | grep ERROR
   ```

2. Try simpler operation first (resize only)

3. Check image isn't corrupted:
   ```bash
   docker exec imagemagick-webgui-app-1 magick identify /path/to/image
   ```

### Timeout

**Error:** `Operation timed out`

**Solutions:**

1. Increase timeout in .env:
   ```env
   IMAGEMAGICK_TIMEOUT=120
   ```

2. Use smaller image or simpler operations

3. For batch processing, reduce concurrent jobs

### Out of Memory

**Error:** `Memory allocation failed` or container killed

**Solutions:**

1. Increase Docker memory limit
2. Reduce IMAGEMAGICK_MEMORY_LIMIT
3. Process smaller images
4. Reduce batch size

### Preview Doesn't Match Result

**Issue:** What you see isn't what you get

**Explanation:** Preview uses CSS filters, result uses ImageMagick. They're similar but not identical.

**Solutions:**

1. Use "Command Preview" to see actual command
2. Test with single image first
3. Adjust values slightly if needed

---

## 🤖 AI Issues

### AI Service Not Available

**Error:** `AI service not available` or `503`

**Solutions:**

1. Check AI status:
   ```bash
   curl http://localhost:8000/api/operations/ai-status
   ```

2. Verify rembg is installed:
   ```bash
   docker exec imagemagick-webgui-app-1 pip show rembg
   ```

3. Check model files:
   ```bash
   docker exec imagemagick-webgui-app-1 ls -la /home/appuser/.u2net/
   ```

4. Restart container to re-download models

### Background Removal Poor Quality

**Issue:** Edges are jagged, parts missing

**Solutions:**

1. Use higher resolution source image
2. Ensure subject has good contrast with background
3. Check if pymatting is available (enables alpha matting)
4. Crop to focus on subject first

### Remove Background Timeout

**Error:** Timeout after 300s

**Solutions:**

1. Reduce image size (max 2048px recommended)
2. Check system resources (needs ~1.5GB RAM)
3. Try without alpha matting

---

## 🔐 Authentication Issues

### Can't Login

**Solutions:**

1. Clear browser cookies
2. Check credentials
3. Reset password (if implemented)
4. Check backend logs

### Token Expired

**Error:** `401 Unauthorized`

**Solutions:**

1. Login again to get new token
2. Increase token expiry:
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=120
   ```

### Google OAuth Not Working

**Solutions:**

1. Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
2. Check redirect URIs in Google Console
3. Ensure callback URL matches

---

## 🎨 UI Issues

### Dark Mode Not Working

**Solutions:**

1. Clear localStorage: `localStorage.clear()`
2. Check browser preferences
3. Toggle manually in Settings

### Images Not Loading

**Solutions:**

1. Hard refresh: Ctrl+Shift+R
2. Check network tab for errors
3. Verify backend is running

### Editor Not Saving

**Solutions:**

1. Wait for operation to complete
2. Check browser console for errors
3. Verify you have edit permissions

---

## 🔧 Terminal Mode Issues

### Command Not Allowed

**Error:** `Operation not allowed`

**Explanation:** Only whitelisted ImageMagick operations are permitted for security.

**Allowed operations:** resize, crop, rotate, flip, blur, sharpen, brightness, contrast, saturation, format, quality, watermark, etc.

**Not allowed:** file operations, shell commands, network access

### Command Syntax Error

**Solutions:**

1. Check ImageMagick documentation
2. Use Command Preview to validate
3. Escape special characters properly
4. Don't include input/output filenames (added automatically)

---

## 📊 Performance Issues

### Slow Processing

**Solutions:**

1. Reduce image size before processing
2. Limit concurrent operations
3. Increase Docker resources
4. Use SSD storage

### High Memory Usage

**Solutions:**

1. Limit batch size
2. Reduce IMAGEMAGICK_MEMORY_LIMIT
3. Clear temporary files:
   ```bash
   docker exec imagemagick-webgui-app-1 rm -rf /tmp/imagemagick/*
   ```

### Slow Uploads

**Solutions:**

1. Compress images before upload
2. Use wired connection
3. Check server bandwidth

---

## 🐛 Reporting Bugs

If you can't solve the issue:

1. **Gather information:**
   - Docker logs: `docker compose logs > logs.txt`
   - Browser console errors
   - Steps to reproduce
   - Screenshots

2. **Check existing issues:**
   [GitHub Issues](https://github.com/przemekskw/imagemagick-webui/issues)

3. **Create new issue:**
   Include all gathered information

---

## 📞 Getting Help

- **GitHub Issues:** Bug reports and feature requests
- **Discussions:** Questions and community help
- **API Docs:** http://localhost:8000/docs

---

## Next Steps

- [[Installation]] - Reinstall if needed
- [[Configuration]] - Check settings
- [[AI Features]] - AI-specific help
