# Format Conversion

Convert images between different file formats with quality control.

---

## Supported Formats

### Input Formats

| Format | Extensions | Notes |
|--------|------------|-------|
| JPEG | .jpg, .jpeg | Most common photo format |
| PNG | .png | Lossless with transparency |
| WebP | .webp | Modern web format |
| GIF | .gif | Animations supported |
| TIFF | .tiff, .tif | High-quality archival |
| PDF | .pdf | Document format (rasterized) |
| SVG | .svg | Vector graphics |
| AVIF | .avif | Next-gen format |
| BMP | .bmp | Uncompressed bitmap |

### Output Formats

| Format | Transparency | Animation | Best For |
|--------|--------------|-----------|----------|
| **WebP** | ✅ Yes | ✅ Yes | Web, best compression |
| **PNG** | ✅ Yes | ❌ No | Lossless, transparency |
| **JPEG** | ❌ No | ❌ No | Photos, compatibility |
| **GIF** | ✅ 1-bit | ✅ Yes | Simple animations |
| **AVIF** | ✅ Yes | ✅ Yes | Modern browsers |

---

## Format Comparison

### File Size (typical 1920×1080 photo)

| Format | Quality 85% | Quality 100% |
|--------|-------------|--------------|
| JPEG | ~200 KB | ~800 KB |
| PNG | N/A | ~3 MB |
| WebP | ~120 KB | ~600 KB |
| AVIF | ~80 KB | ~400 KB |

### Quality vs Size

```
Quality:  AVIF > WebP ≈ JPEG > GIF
Size:     AVIF < WebP < JPEG < PNG
Support:  JPEG > PNG > GIF > WebP > AVIF
```

---

## Choosing Output Format

### WebP (Recommended for Web)

✅ **Pros:**
- Smallest file size
- Supports transparency
- Supports animation
- Good browser support (95%+)

❌ **Cons:**
- Not supported by older browsers
- Some software doesn't open it

**Best for:** Websites, web apps, modern platforms

### JPEG

✅ **Pros:**
- Universal support
- Good for photos
- Small file size

❌ **Cons:**
- No transparency
- Lossy compression
- Quality degrades with re-saves

**Best for:** Photos, social media, email

### PNG

✅ **Pros:**
- Lossless quality
- Full transparency
- No compression artifacts

❌ **Cons:**
- Large file size
- No animation

**Best for:** Logos, graphics, screenshots, archival

### GIF

✅ **Pros:**
- Animation support
- Universal support
- Transparency (1-bit)

❌ **Cons:**
- 256 color limit
- Large file size for animations
- Poor for photos

**Best for:** Simple animations, icons

### AVIF

✅ **Pros:**
- Best compression
- Excellent quality
- Supports HDR

❌ **Cons:**
- Limited browser support (~85%)
- Slow encoding

**Best for:** Cutting-edge web projects

---

## Quality Settings

### Quality Slider (1-100%)

| Range | Use Case |
|-------|----------|
| 100% | Archival, print |
| 90-95% | High quality |
| 80-90% | Web standard |
| 60-80% | Social media |
| 40-60% | Thumbnails |
| <40% | Previews only |

### Format-Specific Recommendations

| Format | Recommended | Notes |
|--------|-------------|-------|
| JPEG | 82-85% | Best quality/size balance |
| WebP | 80-85% | Slightly better than JPEG |
| PNG | N/A | Always lossless |
| AVIF | 75-80% | Lower number still high quality |

---

## Converting Images

### From Dashboard

1. Select image(s)
2. Go to **Terminal** tab
3. Choose **Output Format**
4. Adjust **Quality**
5. Click **Apply**

### From Editor

1. Open image
2. Make edits
3. Click **Download**
4. Choose format and quality

### Batch Conversion

```
1. Upload all images
2. Select All
3. Terminal tab:
   - Output Format: WebP
   - Quality: 85%
4. Apply to all
5. Download as ZIP
```

---

## Terminal Commands

### Basic Conversion

```bash
# Just change format (uses default quality)
# No command needed - just change output format
```

### With Quality

```bash
-quality 85
```

### Strip Metadata

```bash
-strip -quality 85
```

### Interlaced (Progressive)

```bash
-interlace Plane -quality 85
```

### Optimize PNG

```bash
-strip -define png:compression-level=9
```

---

## Special Conversions

### PNG to JPEG (handling transparency)

Transparent areas become white:
```bash
-background white -alpha remove -alpha off
```

Or choose color:
```bash
-background "#f0f0f0" -alpha remove -alpha off
```

### JPEG to PNG (no quality loss)

Simply change format - quality is already lost in JPEG.

### Animated GIF to WebP

WebP supports animation with better compression:
```bash
# Convert via output format selection
```

### PDF to Image

PDFs are rasterized at 150 DPI:
```bash
-density 150 input.pdf[0] output.png
```

---

## Web Optimization

### Responsive Images

Create multiple sizes:
```
Original → 1920px (full)
         → 1280px (desktop)
         → 800px (tablet)
         → 400px (mobile)
```

### Recommended Settings by Platform

| Platform | Format | Quality | Max Size |
|----------|--------|---------|----------|
| General Web | WebP | 82% | 1920px |
| Instagram | JPEG | 85% | 1080px |
| Twitter | JPEG | 85% | 1600px |
| Email | JPEG | 75% | 800px |
| Thumbnails | WebP | 75% | 300px |

---

## Metadata

### Preserving Metadata

EXIF data (camera info, GPS, etc.) is preserved by default.

### Stripping Metadata

For privacy or smaller files:
```bash
-strip
```

**Removes:**
- EXIF data
- Camera information
- GPS coordinates
- Color profiles
- Thumbnails

---

## Troubleshooting

### Large Output Files

- Lower quality setting
- Use WebP instead of PNG
- Resize before converting
- Strip metadata

### Quality Loss

- Use PNG for lossless
- Don't re-compress JPEGs multiple times
- Use higher quality setting

### Transparency Lost

- Use PNG or WebP (not JPEG)
- Check alpha channel preserved

### Colors Look Different

- Color profile conversion
- Use `-strip` to remove profiles
- Or use `-colorspace sRGB`

---

## Tips

1. **WebP for web** - Best compression with transparency
2. **JPEG for photos** - Universal compatibility
3. **PNG for graphics** - Lossless with transparency
4. **85% quality** - Sweet spot for most uses
5. **Strip metadata** - Smaller files, better privacy
6. **Resize first** - Then convert for smaller files

---

## Next Steps

- [[Batch Processing]] - Convert multiple images
- [[Terminal Mode]] - Advanced conversion options
- [[Resize and Crop]] - Prepare images before converting
