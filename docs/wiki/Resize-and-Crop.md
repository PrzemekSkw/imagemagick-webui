# Resize and Crop

Control image dimensions with precision.

---

## Resize

### Methods

#### By Dimensions

Enter exact pixel values:
- **Width**: Target width in pixels
- **Height**: Target height in pixels
- **Lock Aspect Ratio**: Maintain proportions

```
Original: 1920×1080
Target: 800×600

With Lock Ratio ON:
  Result: 800×450 (maintains 16:9)

With Lock Ratio OFF:
  Result: 800×600 (stretched)
```

#### By Percentage

Scale relative to original size:
- **Slider**: 10% to 200%
- **Presets**: 25%, 50%, 75%, 100%, 150%, 200%

```
Original: 2000×1000
Scale: 50%
Result: 1000×500
```

---

### Fit Modes

| Mode | Behavior | Best For |
|------|----------|----------|
| **Contain** | Fit entirely within dimensions | Preserving full image |
| **Cover** | Fill dimensions, crop excess | Thumbnails, avatars |
| **Fill** | Stretch to exact dimensions | Specific requirements |

#### Visual Comparison

```
Original 1920×1080 → Target 800×800

Contain (fit inside):
┌────────────────┐
│░░░░░░░░░░░░░░░░│  ← letterbox
│████████████████│
│████████████████│
│░░░░░░░░░░░░░░░░│  ← letterbox
└────────────────┘
Result: 800×450 on 800×800 canvas

Cover (fill & crop):
┌────────────────┐
│  ████████████  │  ← cropped sides
│  ████████████  │
│  ████████████  │
│  ████████████  │
└────────────────┘
Result: 800×800 (cropped from center)

Fill (stretch):
┌────────────────┐
│████████████████│
│████████████████│  ← distorted
│████████████████│
│████████████████│
└────────────────┘
Result: 800×800 (stretched)
```

---

### Common Presets

| Use Case | Dimensions | Mode |
|----------|------------|------|
| Full HD | 1920×1080 | Contain |
| HD | 1280×720 | Contain |
| Instagram Square | 1080×1080 | Cover |
| Instagram Portrait | 1080×1350 | Cover |
| Facebook Cover | 820×312 | Cover |
| Twitter Header | 1500×500 | Cover |
| Thumbnail | 300×300 | Cover |
| Avatar | 150×150 | Cover |

---

## Crop

### Interactive Crop

1. Click **"Enable Crop"** in Editor → Transform tab
2. **Drag corners** to adjust selection
3. **Drag center** to move selection
4. Click **"Apply Crop"**

```
┌─────────────────────────────┐
│                             │
│    ○═══════════════○        │
│    ║               ║        │
│    ║   CROP AREA   ║        │
│    ║               ║        │
│    ○═══════════════○        │
│                             │
└─────────────────────────────┘
     ↑ drag corners to resize
```

### Aspect Ratio Lock

Lock crop to specific ratio:
- **Free** - Any dimensions
- **1:1** - Square
- **4:3** - Standard photo
- **16:9** - Widescreen
- **3:2** - Classic 35mm
- **Custom** - Enter your own

### Crop Presets

| Preset | Ratio | Common Use |
|--------|-------|------------|
| Square | 1:1 | Instagram, avatars |
| Portrait | 2:3 | Pinterest, stories |
| Landscape | 3:2 | Standard photos |
| Widescreen | 16:9 | YouTube, presentations |
| Ultrawide | 21:9 | Banners, headers |

---

## Terminal Commands

### Resize

```bash
# Resize to width, auto height
-resize 800x

# Resize to height, auto width
-resize x600

# Resize to fit within (contain)
-resize 800x600

# Resize to fill (cover)
-resize 800x600^

# Resize exact (fill/stretch)
-resize 800x600!

# Resize by percentage
-resize 50%

# Only shrink if larger
-resize 800x600>

# Only enlarge if smaller
-resize 800x600<
```

### Crop

```bash
# Crop from center
-gravity center -crop 800x600+0+0 +repage

# Crop from top-left
-crop 800x600+0+0 +repage

# Crop with offset
-crop 800x600+100+50 +repage

# Crop percentage
-crop 50%x50%+25%+25% +repage
```

### Resize + Crop (Cover)

```bash
# Resize to cover, then crop to exact
-resize 800x600^ -gravity center -extent 800x600
```

---

## Quality Considerations

### Upscaling

⚠️ **Warning:** Enlarging images reduces quality.

| Scale | Quality Impact |
|-------|---------------|
| 100-120% | Minimal loss |
| 120-150% | Noticeable softness |
| 150-200% | Significant degradation |
| >200% | Not recommended |

**Tip:** Use AI Upscale for better results when enlarging.

### Downscaling

✅ Reducing size generally maintains quality.

| Algorithm | Quality | Speed |
|-----------|---------|-------|
| Lanczos | Best | Slower |
| Mitchell | Good | Fast |
| Point | Pixelated | Fastest |

---

## Batch Resize

### All to Same Size

```
1. Select multiple images
2. Resize → 800×600, Cover mode
3. Apply to all
```

### Thumbnails

```
1. Select images
2. Resize → 300×300, Cover mode
3. Apply to all
4. Download as ZIP
```

---

## Tips

1. **Preserve originals** - Resizing creates new files
2. **Use Cover for thumbnails** - Ensures consistent dimensions
3. **Check aspect ratio** - Avoid distortion
4. **Batch similar images** - More efficient
5. **Quality matters** - Start with highest quality source

---

## Next Steps

- [[Image Editor]] - Full editing features
- [[Batch Processing]] - Resize multiple images
- [[Format Conversion]] - Output format options
