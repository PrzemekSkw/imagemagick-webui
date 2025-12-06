# Image Editor

The full-featured image editor provides real-time preview and advanced editing capabilities.

---

## Opening the Editor

1. **From Dashboard:** Click the ✏️ Edit button on any image
2. **Double-click:** Double-click an image thumbnail
3. **From History:** Click "Edit" on any history item

---

## Editor Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Image Name | Save | Download | Close               │
├─────────────────────────────────────────┬───────────────────┤
│                                         │                   │
│                                         │   Editor Tabs     │
│         Image Preview                   │                   │
│         (with live updates)             │   - Adjust        │
│                                         │   - Resize        │
│                                         │   - Transform     │
│                                         │   - Text          │
│                                         │   - AI            │
│                                         │                   │
├─────────────────────────────────────────┴───────────────────┤
│  Zoom Controls | Reset | Undo                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Editor Tabs

### Adjust Tab

Fine-tune image appearance with real-time preview:

| Control | Range | Default | Description |
|---------|-------|---------|-------------|
| Brightness | 0-200% | 100% | Light/dark adjustment |
| Contrast | 0-200% | 100% | Difference between tones |
| Saturation | 0-200% | 100% | Color intensity |
| Hue | -180° to 180° | 0° | Color shift |
| Blur | 0-30px | 0px | Gaussian blur |

**Quick Actions:**
- **Reset All** - Return to original values
- **Auto Enhance** - One-click improvement

### Resize Tab

| Option | Description |
|--------|-------------|
| **Width** | Target width in pixels |
| **Height** | Target height in pixels |
| **Lock Ratio** | Maintain aspect ratio |
| **Percent** | Scale by percentage |

**Fit Modes:**
- **Contain** - Fit within dimensions (may have letterboxing)
- **Cover** - Fill dimensions (may crop edges)
- **Fill** - Stretch to exact dimensions

**Presets:**
- 1920×1080 (Full HD)
- 1280×720 (HD)
- 800×600 (Web)
- 400×400 (Thumbnail)

### Transform Tab

| Operation | Description |
|-----------|-------------|
| **Rotate 90° CW** | Rotate clockwise |
| **Rotate 90° CCW** | Rotate counter-clockwise |
| **Rotate 180°** | Flip upside-down |
| **Flip Horizontal** | Mirror left-right |
| **Flip Vertical** | Mirror top-bottom |

**Crop Tool:**
1. Click "Enable Crop"
2. Drag corners to adjust area
3. Click "Apply Crop"

### Text Tab

Add watermarks to your images:

| Option | Description |
|--------|-------------|
| **Text** | Watermark content |
| **Position** | 9-point grid selector |
| **Font Size** | 8-72pt |
| **Opacity** | 10-100% transparency |

**Position Grid:**
```
┌────────┬────────┬────────┐
│   NW   │   N    │   NE   │
├────────┼────────┼────────┤
│   W    │ Center │   E    │
├────────┼────────┼────────┤
│   SW   │   S    │   SE   │
└────────┴────────┴────────┘
```

### AI Tab

AI-powered features:

| Feature | Description | Time |
|---------|-------------|------|
| **Remove Background** | AI background removal | 30-60s |
| **Upscale 2x** | Double resolution | 5-10s |
| **Upscale 4x** | Quadruple resolution | 10-20s |
| **Auto Enhance** | Automatic improvements | <1s |

**Remove Background:**
- Works best with clear subjects
- Output is PNG with transparency
- May take up to 60 seconds

---

## Preview Area

### Zoom Controls

| Button | Action |
|--------|--------|
| **+** | Zoom in |
| **-** | Zoom out |
| **Fit** | Fit to window |
| **100%** | Actual size |

### Navigation
- **Mouse wheel** - Zoom in/out
- **Click & drag** - Pan when zoomed

---

## Saving Changes

### Save Button
- Saves edited image as new file
- Original remains unchanged
- New image appears in gallery

### Download Button
- Downloads directly to computer
- Choose format: WebP, PNG, JPG
- Adjust quality: 1-100%

### Close Button
- Returns to dashboard
- **Warning:** Unsaved changes will be lost

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + S` | Save changes |
| `Ctrl + Z` | Undo last action |
| `Escape` | Close editor |
| `+` / `-` | Zoom in/out |
| `0` | Reset zoom |

---

## Tips

1. **Non-destructive editing** - Original images are never modified
2. **Real-time preview** - See changes before saving
3. **Combine operations** - Apply multiple adjustments before saving
4. **AI features** - Give it time, complex operations take longer

---

## Next Steps

- [[AI Features]] - Learn about AI capabilities
- [[Batch Processing]] - Edit multiple images
- [[Dashboard Overview]] - Return to main interface
