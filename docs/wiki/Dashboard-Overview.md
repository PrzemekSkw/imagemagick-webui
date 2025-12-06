# Dashboard Overview

The main dashboard is your central hub for image management and processing.

---

## Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Header (Logo, Search, Theme Toggle, User Menu)             │
├──────────┬──────────────────────────────┬───────────────────┤
│          │                              │                   │
│ Sidebar  │     Image Gallery            │  Quick Operations │
│          │                              │     Panel         │
│ - Home   │  ┌─────┐ ┌─────┐ ┌─────┐    │                   │
│ - History│  │ img │ │ img │ │ img │    │  - Resize         │
│ - Settings│ └─────┘ └─────┘ └─────┘    │  - Rotate         │
│          │                              │  - Text           │
│          │     Upload Zone              │  - Terminal       │
│          │                              │                   │
└──────────┴──────────────────────────────┴───────────────────┘
```

---

## Components

### Header

| Element | Function |
|---------|----------|
| Logo | Click to return to dashboard |
| Theme Toggle | Switch between Light/Dark/Auto mode |
| User Menu | Profile, Settings, Logout |

### Sidebar

| Item | Description |
|------|-------------|
| **Home** | Main dashboard with gallery |
| **History** | View processed images (24h) |
| **Settings** | App preferences |

### Image Gallery

- **Grid view** of uploaded images with thumbnails
- **Checkbox selection** - click to select multiple images
- **Hover actions** - Edit, Download, Delete buttons
- **Drag & drop** - Upload new images directly

### Upload Zone

- Click or drag files to upload
- Supports: JPG, PNG, WebP, GIF, TIFF, PDF, SVG, AVIF
- Multiple file upload
- Progress indicator during upload

### Quick Operations Panel

Right sidebar with common operations:
- **Resize** - Dimensions or percentage
- **Rotate** - 90°/180°/270° + flip
- **Text** - Watermark overlay
- **Terminal** - Raw ImageMagick commands

---

## Selecting Images

### Single Selection
Click on an image thumbnail to select it.

### Multiple Selection
- **Ctrl + Click** - Add/remove individual images
- **Shift + Click** - Select range of images
- **Select All** - Use "Select All" button in header

### Selection Indicator
- Selected images show a blue border
- Counter shows "X image(s) selected" in operations panel

---

## Image Actions

### Per-Image Actions (hover)

| Button | Action |
|--------|--------|
| ✏️ Edit | Open full image editor |
| ⬇️ Download | Download original file |
| 🗑️ Delete | Remove from gallery |

### Bulk Actions (selection)

| Button | Action |
|--------|--------|
| **Apply** | Run selected operation on all selected images |
| **Download ZIP** | Download all selected as ZIP archive |
| **Delete Selected** | Remove all selected images |

---

## Quick Operations

### Resize Tab

**Dimensions Mode:**
- Enter exact width × height
- Toggle "Preserve Aspect Ratio"
- Choose fit mode: Contain, Cover, Fill

**Percentage Mode:**
- Slider from 10% to 200%
- Quick presets: 25%, 50%, 75%, 100%

### Rotate Tab

**Rotation:**
- 90° clockwise
- 180°
- 90° counter-clockwise

**Flip:**
- Horizontal (mirror)
- Vertical (upside-down)

### Text Tab

- Enter watermark text
- Choose position (3×3 grid)
- Adjust font size (8-72pt)

### Terminal Tab

- Raw ImageMagick command input
- Quick command buttons
- Output format selector
- Quality slider

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + A` | Select all images |
| `Delete` | Delete selected images |
| `Escape` | Deselect all |

---

## Tips

1. **Batch processing** - Select multiple images, apply same operation to all
2. **Quick edit** - Double-click image to open editor
3. **Drag to reorder** - Organize your workflow
4. **Right-click menu** - Additional options per image

---

## Next Steps

- [[Image Editor]] - Learn the full editor
- [[Batch Processing]] - Process multiple images
- [[Quick Start Guide]] - Get started quickly
