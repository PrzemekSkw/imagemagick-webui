# Filters and Effects

Apply visual effects and adjustments to your images.

---

## Basic Adjustments

Available in Editor → Adjust tab with real-time preview.

### Brightness

Controls overall lightness/darkness.

| Value | Effect |
|-------|--------|
| 0% | Completely black |
| 50% | Darker |
| 100% | Original |
| 150% | Brighter |
| 200% | Very bright |

### Contrast

Controls difference between light and dark areas.

| Value | Effect |
|-------|--------|
| 0% | Flat, gray |
| 50% | Low contrast |
| 100% | Original |
| 150% | High contrast |
| 200% | Extreme contrast |

### Saturation

Controls color intensity.

| Value | Effect |
|-------|--------|
| 0% | Grayscale |
| 50% | Muted colors |
| 100% | Original |
| 150% | Vivid colors |
| 200% | Oversaturated |

### Hue

Shifts all colors around the color wheel.

| Value | Effect |
|-------|--------|
| -180° | Inverted hue |
| -90° | Shift toward blue |
| 0° | Original |
| +90° | Shift toward yellow |
| +180° | Inverted hue |

### Blur

Gaussian blur effect.

| Value | Effect |
|-------|--------|
| 0px | Sharp (original) |
| 1-3px | Subtle softening |
| 5-10px | Moderate blur |
| 15-30px | Heavy blur |

---

## Color Filters

### Grayscale

Convert to black and white.

```bash
# Terminal command
-colorspace Gray
```

### Sepia

Classic vintage brown tone.

| Threshold | Effect |
|-----------|--------|
| 50% | Light sepia |
| 80% | Classic sepia |
| 100% | Full sepia |

```bash
# Terminal command
-sepia-tone 80%
```

### Vintage

Combine effects for old photo look:
1. Reduce saturation to 80%
2. Add sepia at 30%
3. Slight blur (0.5px)
4. Reduce contrast slightly

---

## Artistic Effects

### Charcoal

Pencil/charcoal sketch effect.

```bash
# Terminal command
-charcoal 2
```

| Factor | Effect |
|--------|--------|
| 1 | Fine detail |
| 2 | Standard |
| 5 | Bold strokes |

### Edge Detection

Highlights edges in image.

```bash
# Terminal command
-edge 3
```

### Emboss

3D raised effect.

```bash
# Terminal command
-emboss 0x1
```

### Oil Paint

Simulates oil painting.

```bash
# Terminal command
-paint 4
```

| Radius | Effect |
|--------|--------|
| 1-2 | Subtle |
| 3-5 | Moderate |
| 6+ | Heavy |

### Posterize

Reduces color levels for poster effect.

```bash
# Terminal command
-posterize 4
```

| Levels | Colors |
|--------|--------|
| 2 | 8 colors |
| 4 | 64 colors |
| 8 | 512 colors |

---

## Sharpening

### Unsharp Mask

Professional sharpening technique.

```bash
# Subtle sharpening
-unsharp 0x0.5+0.5+0.008

# Standard sharpening
-unsharp 0x1+1+0.05

# Strong sharpening
-unsharp 0x2+2+0.05
```

Parameters: `radiusxsigma+amount+threshold`

### Simple Sharpen

Quick sharpening.

```bash
# Terminal command
-sharpen 0x2
```

---

## Special Effects

### Negate (Invert)

Inverts all colors.

```bash
# Terminal command
-negate
```

### Solarize

Partial color inversion for surreal effect.

```bash
# Terminal command
-solarize 50%
```

### Vignette

Darkened corners effect.

```bash
# Terminal command
-vignette 0x50
```

### Noise

Add random noise/grain.

```bash
# Terminal command
-noise 3
```

| Type | Effect |
|------|--------|
| Gaussian | Smooth noise |
| Impulse | Salt & pepper |
| Random | Film grain |

---

## Filter Combinations

### Instagram-style Filters

#### Warm Vintage
```bash
-modulate 105,110,100 -sepia-tone 20% -contrast-stretch 0
```

#### Cool Blue
```bash
-modulate 100,100,115 -brightness-contrast 5x5
```

#### High Contrast B&W
```bash
-colorspace Gray -contrast-stretch 2%x1%
```

#### Faded Film
```bash
-modulate 100,80,100 -level 5%,95% -brightness-contrast -5x-5
```

### Professional Presets

#### Portrait Enhancement
```bash
-modulate 100,110,100 -unsharp 0x0.5+0.5+0.01 -brightness-contrast 5x5
```

#### Landscape Pop
```bash
-modulate 100,130,100 -contrast-stretch 1% -unsharp 0x1+0.5+0.01
```

#### Product Photo
```bash
-normalize -modulate 100,105,100 -unsharp 0x0.5+1+0.01
```

---

## Performance

### Filter Speed

| Effect | Speed | Memory |
|--------|-------|--------|
| Brightness/Contrast | ⚡ Fast | Low |
| Blur (small) | ⚡ Fast | Low |
| Blur (large) | 🐢 Slow | High |
| Sharpen | ⚡ Fast | Low |
| Charcoal | 🐌 Medium | Medium |
| Oil Paint | 🐢 Slow | High |

### Tips for Large Images

1. **Resize first** - Apply effects to smaller version
2. **Preview on crop** - Test on portion of image
3. **Simple effects** - Complex chains take longer

---

## Quality Tips

1. **Order matters** - Apply effects in logical order
2. **Subtle is better** - Small adjustments look professional
3. **Check on multiple devices** - Colors vary by display
4. **Save originals** - Always keep unedited copies
5. **Use PNG for editing** - Avoid compression artifacts

---

## Comparison: Before/After

Use the Editor to compare:
1. Apply effects
2. Toggle preview on/off
3. Compare before saving

---

## Next Steps

- [[Image Editor]] - Apply effects with preview
- [[Terminal Mode]] - Advanced effect commands
- [[Batch Processing]] - Apply to multiple images
