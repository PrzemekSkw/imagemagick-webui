# AI Features

ImageMagick WebGUI includes AI-powered features for advanced image processing.

---

## 🪄 Background Removal

Remove backgrounds from images with one click using [rembg](https://github.com/danielgatis/rembg).

### How to Use

1. Open an image in the **Editor**
2. Go to the **AI** tab
3. Click **Remove Background**
4. Wait 30-60 seconds for processing
5. Download the result (PNG with transparency)

### How It Works

The feature uses the **U2-Net** deep learning model:
- Trained on 10,000+ images
- Works best with clear foreground subjects
- Outputs PNG with alpha channel

### Alpha Matting

For smoother edges, alpha matting is automatically applied when available:
- Refines edge detection
- Reduces jagged borders
- Better hair/fur handling

### Best Practices

✅ **Works well with:**
- Product photos
- Portraits
- Objects on simple backgrounds
- High contrast images

⚠️ **May struggle with:**
- Complex backgrounds
- Transparent objects (glass, water)
- Very fine details (individual hairs)
- Low contrast images

### Troubleshooting

**"AI service not available"**
- Check diagnostics: `GET /api/operations/ai-status`
- Verify rembg is installed
- Check model files exist in `~/.u2net/`

**Poor results**
- Try with higher resolution image
- Ensure good lighting in original
- Crop to focus on subject first

---

## 🔍 AI Upscaling

Increase image resolution using intelligent upscaling.

### How to Use

1. Open an image in the **Editor**
2. Go to the **AI** tab
3. Select scale: **2x** or **4x**
4. Click **Upscale**

### Technology

Uses **LANCZOS** resampling with:
- Intelligent edge detection
- Unsharp masking for clarity
- Contrast preservation

### Limits

| Original Size | 2x Result | 4x Result |
|--------------|-----------|-----------|
| 1000×1000 | 2000×2000 | 4000×4000 |
| 2000×2000 | 4000×4000 | 8000×8000 |

Maximum output: 8192×8192 pixels

### Tips

- Start with highest quality original
- 2x usually gives better quality than 4x
- Works best on photos, less on text/graphics

---

## ✨ Auto Enhance

Automatically improve image quality with one click.

### What It Does

1. **Normalize** - Stretch histogram for full dynamic range
2. **Saturation boost** - +10% color vibrancy
3. **Unsharp mask** - Subtle sharpening for clarity

### When to Use

- Quick improvement for dull photos
- Preparing images for web/social media
- Batch processing large collections

### Before/After

The enhancement is subtle but noticeable:
- Brighter shadows
- More vivid colors
- Sharper details

---

## 🔧 AI Diagnostics

Check AI service status:

```bash
curl http://localhost:8000/api/operations/ai-status
```

Response:
```json
{
  "available": true,
  "diagnostics": {
    "rembg_available": true,
    "rembg_version": "2.0.50",
    "pymatting_available": true,
    "session_loaded": true,
    "u2net_home": "/home/appuser/.u2net",
    "models_dir_exists": true,
    "models_found": [
      "/home/appuser/.u2net/u2net.onnx"
    ]
  }
}
```

### Required Components

| Component | Purpose | Required |
|-----------|---------|----------|
| `rembg` | Background removal | Yes |
| `onnxruntime` | ML inference | Yes |
| `pymatting` | Alpha matting | Optional |
| `u2net.onnx` | Model file (~170MB) | Yes |

### Model Download

Models download automatically on first use. Manual download:

```bash
# Inside container
python -c "from rembg import new_session; new_session('u2net')"
```

---

## Performance

### Processing Times (typical)

| Operation | 1080p Image | 4K Image |
|-----------|-------------|----------|
| Background Removal | 15-30s | 45-90s |
| Upscale 2x | 2-5s | 10-20s |
| Auto Enhance | <1s | 2-3s |

### Memory Usage

- Background removal: ~1.5GB RAM
- Upscaling: ~500MB RAM
- Enhance: ~200MB RAM

### GPU Support

Currently CPU-only. GPU support planned for future versions.

---

## Limitations

1. **No batch AI processing** - One image at a time
2. **CPU only** - No GPU acceleration yet
3. **Size limits** - Images resized to max 2048px for processing
4. **Model variety** - Only U2-Net model currently

---

## Future Roadmap

- [ ] GPU acceleration (CUDA)
- [ ] More background removal models
- [ ] Real-ESRGAN for better upscaling
- [ ] Face enhancement
- [ ] Object detection/cropping
- [ ] Style transfer

---

## Next Steps

- [[Image Editor]] - Using the full editor
- [[REST API]] - API documentation
- [[Troubleshooting]] - Common issues
