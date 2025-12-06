# Terminal Mode

For power users who know ImageMagick commands directly.

---

## Overview

Terminal Mode provides:
- Direct access to ImageMagick operations
- Full command preview before execution
- Quick command buttons for common operations
- Output format and quality control

---

## Accessing Terminal Mode

1. **Dashboard:** Quick Operations → Terminal tab
2. **Editor:** Not available (use Adjust/Transform tabs)

---

## Interface

```
┌─────────────────────────────────────────┐
│  Terminal                               │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐│
│  │ $ -sepia-tone 80%                   ││
│  │                                     ││
│  └─────────────────────────────────────┘│
│                                         │
│  Quick Commands:                        │
│  [Sepia] [Charcoal] [Edge] [Emboss]    │
│  [Negate] [Posterize] [Solarize]       │
│                                         │
│  Output Format: [WebP ▼]                │
│  Quality: ████████░░ 85%                │
│                                         │
│  Command Preview:                       │
│  magick input.jpg -sepia-tone 80%      │
│  -quality 85 output.webp                │
│                                         │
│  [Apply to X image(s)]                  │
└─────────────────────────────────────────┘
```

---

## Writing Commands

### Basic Syntax

Enter ImageMagick operations **without** input/output files:

```bash
# ✅ Correct - just the operation
-sepia-tone 80%

# ❌ Wrong - don't include filenames
magick input.jpg -sepia-tone 80% output.jpg
```

### Multiple Operations

Chain operations with spaces:

```bash
-resize 800x600 -quality 85 -sharpen 0x1
```

---

## Quick Commands

| Button | Command | Effect |
|--------|---------|--------|
| **Sepia** | `-sepia-tone 80%` | Vintage brown tone |
| **Charcoal** | `-charcoal 2` | Pencil sketch effect |
| **Edge** | `-edge 3` | Edge detection |
| **Emboss** | `-emboss 0x1` | 3D embossed effect |
| **Negate** | `-negate` | Invert colors |
| **Posterize** | `-posterize 4` | Reduce color levels |
| **Solarize** | `-solarize 50%` | Partial color inversion |

---

## Common Commands

### Color Adjustments

```bash
# Grayscale
-colorspace Gray

# Increase saturation
-modulate 100,150,100

# Decrease brightness
-modulate 80,100,100

# Adjust hue (rotate colors)
-modulate 100,100,150
```

### Effects

```bash
# Gaussian blur
-blur 0x8

# Sharpen
-sharpen 0x2

# Add noise
-noise 3

# Oil painting effect
-paint 4

# Pixelate
-scale 10% -scale 1000%
```

### Borders & Frames

```bash
# Simple border
-border 10x10 -bordercolor "#000000"

# Rounded corners
-alpha set -background none \
  \( +clone -alpha extract -draw "fill black polygon 0,0 0,15 15,0 fill white circle 15,15 15,0" \
  \( +clone -flip \) -compose Multiply -composite \
  \( +clone -flop \) -compose Multiply -composite \) \
  -alpha off -compose CopyOpacity -composite

# Shadow effect
\( +clone -background black -shadow 80x3+5+5 \) +swap -background none -layers merge +repage
```

### Text & Annotations

```bash
# Add text
-gravity southeast -pointsize 24 -fill white -annotate +10+10 "© 2024"

# With shadow
-gravity south -font Arial -pointsize 36 \
  -fill black -annotate +2+12 "Text" \
  -fill white -annotate +0+10 "Text"
```

### Composition

```bash
# Tile pattern
-size 100x100 tile:pattern.png

# Vignette effect
-background black -vignette 0x50
```

---

## Allowed Operations

For security, only these operations are permitted:

### Geometry
`-resize`, `-crop`, `-extent`, `-thumbnail`, `-scale`, `-sample`

### Color
`-colorspace`, `-modulate`, `-brightness-contrast`, `-level`, `-normalize`, `-equalize`, `-auto-level`, `-auto-gamma`

### Effects
`-blur`, `-sharpen`, `-unsharp`, `-gaussian-blur`, `-emboss`, `-edge`, `-charcoal`, `-sketch`, `-paint`, `-noise`

### Adjustments
`-sepia-tone`, `-grayscale`, `-negate`, `-posterize`, `-solarize`, `-threshold`

### Transform
`-rotate`, `-flip`, `-flop`, `-transpose`, `-transverse`

### Format
`-quality`, `-strip`, `-interlace`, `-density`

### Annotation
`-annotate`, `-gravity`, `-font`, `-pointsize`, `-fill`, `-stroke`, `-strokewidth`

### Other
`-border`, `-bordercolor`, `-frame`, `-shadow`, `-vignette`, `-alpha`

---

## Output Settings

### Format Options

| Format | Best For | Transparency |
|--------|----------|--------------|
| **WebP** | Web, best compression | ✅ Yes |
| **PNG** | Lossless, transparency | ✅ Yes |
| **JPEG** | Photos, compatibility | ❌ No |
| **GIF** | Simple animations | ✅ Yes (1-bit) |

### Quality Settings

| Quality | File Size | Use Case |
|---------|-----------|----------|
| 100% | Largest | Archival |
| 85-95% | Large | High quality |
| 70-85% | Medium | Web standard |
| 50-70% | Small | Thumbnails |
| <50% | Smallest | Previews |

---

## Examples

### Vintage Photo Effect

```bash
-sepia-tone 80% -modulate 95,80,100 -blur 0x0.5
```

### HDR-like Effect

```bash
-contrast-stretch 2%x1% -modulate 100,130,100 -unsharp 0x1+1+0.05
```

### Instagram-style Filter

```bash
-modulate 105,110,100 -colorize 5,5,0 -contrast-stretch 0
```

### Professional Sharpening

```bash
-unsharp 0.5x0.5+1.0+0.05
```

### Web Optimization

```bash
-resize 1200x1200> -quality 82 -strip -interlace Plane
```

---

## Troubleshooting

### Command Not Allowed

```
Error: Operation not allowed: -write
```

Only whitelisted operations are permitted. See "Allowed Operations" above.

### Syntax Error

```
Error: Invalid argument: -resize abc
```

Check command syntax in ImageMagick documentation.

### Timeout

```
Error: Operation timed out
```

Simplify command or reduce image size.

---

## Resources

- [ImageMagick Documentation](https://imagemagick.org/script/command-line-options.php)
- [ImageMagick Examples](https://imagemagick.org/Usage/)
- [Fred's ImageMagick Scripts](http://www.fmwconcepts.com/imagemagick/)

---

## Next Steps

- [[Filters and Effects]] - GUI alternatives
- [[Batch Processing]] - Apply to multiple images
- [[REST API]] - Automate with API
