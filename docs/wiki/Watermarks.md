# Watermarks

Add text overlays to protect and brand your images.

---

## Overview

Watermarks help you:
- Protect images from unauthorized use
- Brand your work with copyright
- Add captions or descriptions
- Indicate draft/sample status

---

## Adding Text Watermarks

### From Dashboard

1. Select image(s)
2. Go to **Text** tab in Quick Operations
3. Enter watermark text
4. Choose position
5. Adjust font size
6. Click **Apply**

### From Editor

1. Open image in Editor
2. Go to **Text** tab
3. Configure watermark
4. Adjust opacity
5. Preview in real-time
6. **Save** to apply

---

## Configuration Options

### Text Content

Enter any text:
- Copyright: `© 2024 Your Name`
- Brand: `Your Company`
- Status: `DRAFT` or `SAMPLE`
- Date: `December 2024`

### Position

9-point positioning grid:

```
┌──────────────────────────────┐
│ Northwest   North   Northeast│
│                              │
│ West       Center       East │
│                              │
│ Southwest   South   Southeast│
└──────────────────────────────┘
```

| Position | Best For |
|----------|----------|
| **Southeast** | Standard copyright |
| **Southwest** | Alternative copyright |
| **Center** | Draft/Sample overlays |
| **North** | Headers/titles |
| **South** | Captions |

### Font Size

| Size | Best For |
|------|----------|
| 8-12pt | Small images, subtle |
| 14-18pt | Standard web images |
| 20-32pt | Large images |
| 36-72pt | Bold statements |

**Tip:** Font size should be ~2-3% of image width for visibility without distraction.

### Opacity (Editor only)

| Opacity | Effect |
|---------|--------|
| 10-30% | Very subtle |
| 40-60% | Visible but not distracting |
| 70-80% | Clear and prominent |
| 90-100% | Bold statement |

---

## Watermark Styles

### Copyright Notice

```
Text: © 2024 Your Name
Position: Southeast
Size: 16pt
Opacity: 50%
```

### Draft Watermark

```
Text: DRAFT
Position: Center
Size: 48pt
Opacity: 30%
```

### Company Branding

```
Text: Your Company
Position: Southwest
Size: 14pt
Opacity: 60%
```

---

## Terminal Commands

### Basic Text Watermark

```bash
-gravity southeast -pointsize 24 -fill white -annotate +10+10 "© 2024"
```

### With Shadow

```bash
-gravity southeast -pointsize 24 \
  -fill black -annotate +12+12 "© 2024" \
  -fill white -annotate +10+10 "© 2024"
```

### Semi-transparent

```bash
-gravity southeast -pointsize 24 \
  -fill "rgba(255,255,255,0.5)" -annotate +10+10 "© 2024"
```

### With Background

```bash
-gravity southeast -pointsize 24 \
  -fill white -undercolor "rgba(0,0,0,0.5)" \
  -annotate +10+10 " © 2024 "
```

### Diagonal Watermark

```bash
-gravity center -pointsize 72 -fill "rgba(255,255,255,0.3)" \
  -rotate -45 -annotate 0 "SAMPLE"
```

---

## Image Watermarks

For logo overlays, use Terminal Mode:

### Basic Logo Overlay

```bash
# Composite logo in corner
logo.png -gravity southeast -composite
```

### Semi-transparent Logo

```bash
\( logo.png -alpha set -channel A -evaluate set 50% \) \
  -gravity southeast -composite
```

---

## Batch Watermarking

### Same Watermark on Multiple Images

1. Upload all images
2. Select All
3. Text tab:
   - Text: `© 2024 Your Name`
   - Position: Southeast
   - Size: 18pt
4. Apply to all
5. Download as ZIP

### Different Watermarks

Process images in groups:
1. Select group 1 → Apply watermark A
2. Select group 2 → Apply watermark B

---

## Best Practices

### Visibility

| Background | Text Color | Shadow |
|------------|------------|--------|
| Light | Dark gray | Light |
| Dark | White | Dark |
| Mixed | White + dark shadow | Yes |

### Placement

✅ **Do:**
- Corner placement for copyright
- Away from main subject
- Consistent position across images

❌ **Don't:**
- Cover important content
- Make too large/distracting
- Use clashing colors

### Protection Level

| Goal | Style |
|------|-------|
| Light branding | Small, corner, 30% opacity |
| Standard protection | Medium, corner, 50% opacity |
| Strong protection | Large, center, 60% opacity |
| Proof/Sample | Diagonal, repeated |

---

## Removing Watermarks

⚠️ **Note:** This tool is for adding watermarks, not removing them from others' images.

If you need to remove your own watermark:
1. Use the original unwatermarked file
2. Or use crop/clone tools in external editor

---

## Tips

1. **Consistency** - Use same style across portfolio
2. **Readability** - Test on different backgrounds
3. **Size matters** - Too small = ineffective, too large = ugly
4. **Shadow helps** - Adds visibility on varied backgrounds
5. **Batch apply** - Process all images at once

---

## Common Issues

### Text Not Visible

- Increase font size
- Change color contrast
- Add shadow
- Increase opacity

### Text Too Prominent

- Decrease font size
- Lower opacity
- Move to corner
- Use lighter color

### Inconsistent Placement

- Use same position for all
- Use percentage-based placement
- Create template settings

---

## Next Steps

- [[Image Editor]] - Fine-tune watermarks
- [[Batch Processing]] - Apply to multiple images
- [[Terminal Mode]] - Advanced watermark commands
