# Quick Start Guide

Get started with ImageMagick WebGUI in 5 minutes!

---

## Step 1: Start the Application

```bash
git clone https://github.com/przemekskw/imagemagick-webui.git
cd imagemagick-webui
docker compose up --build
```

Wait for the message:
```
✓ All services started successfully
```

Open **http://localhost:3000** in your browser.

---

## Step 2: Upload Images

1. Click the **upload area** or drag & drop files
2. Supported formats: JPG, PNG, WebP, GIF, TIFF, PDF, SVG
3. Multiple files can be uploaded at once
4. Thumbnails appear in the gallery

---

## Step 3: Basic Operations (Dashboard)

### Resize an Image

1. **Select** one or more images (click thumbnails)
2. Go to **Resize** tab
3. Choose mode:
   - **Dimensions**: Enter width × height
   - **Percent**: Scale by percentage
4. Enable **Preserve Aspect Ratio** to maintain proportions
5. Click **Apply to X image(s)**

### Add Watermark

1. Select images
2. Go to **Text** tab
3. Enter your watermark text
4. Choose position (9-point grid)
5. Adjust font size (8-72pt)
6. Click **Apply**

### Rotate Image

1. Select images
2. Go to **Rotate** tab
3. Click rotation buttons (90°, 180°, 270°)
4. Or use flip buttons (horizontal/vertical)
5. Click **Apply**

---

## Step 4: Advanced Editing (Editor)

1. Click **Edit** button on any image
2. Full editor opens with tabs:

### Adjust Tab
- Brightness, Contrast, Saturation
- Blur, Hue adjustments
- Real-time preview

### Resize Tab
- Precise dimensions
- Percentage scaling
- Fit modes (contain/cover/fill)

### Text Tab
- Add watermark text
- Position selector
- Font size & opacity

### AI Tab
- **Remove Background** - AI-powered background removal
- **Upscale 2x/4x** - Increase resolution
- **Auto Enhance** - One-click improvement

### Transform Tab
- Rotation (free angle)
- Flip horizontal/vertical
- Crop tool

---

## Step 5: Download Results

### Single Image
- Click **Download** button above gallery
- Or right-click → Save Image

### Multiple Images
1. Select all processed images
2. Click **Download as ZIP**

### From History
1. Go to **History** (sidebar)
2. Find your processed images
3. Download within 24 hours

---

## Step 6: Terminal Mode (Advanced)

For power users who know ImageMagick:

1. Select an image
2. Go to **Terminal** tab
3. Type raw ImageMagick commands:
   ```bash
   -sepia-tone 80%
   -charcoal 2
   -edge 3
   -emboss 2
   ```
4. See command preview
5. Click **Apply**

---

## Pro Tips

### Batch Processing
- Select multiple images with Ctrl+Click or Shift+Click
- Apply same operation to all at once
- Use consistent settings for uniform results

### Quality Settings
- For web: WebP format, 80-85 quality
- For print: PNG or high-quality JPG (95+)
- For file size: Lower quality, smaller dimensions

### Workflow
1. Upload all images first
2. Make basic adjustments in Dashboard
3. Fine-tune individual images in Editor
4. Download results

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+A` | Select all images |
| `Delete` | Delete selected |
| `Escape` | Close editor |
| `Ctrl+S` | Save changes (in editor) |
| `Ctrl+Z` | Undo (in editor) |

---

## Common Workflows

### Preparing Images for Web
1. Upload original photos
2. Resize to 1200px width
3. Convert to WebP, quality 80
4. Download

### Adding Watermarks to Portfolio
1. Upload portfolio images
2. Add text watermark: "© Your Name"
3. Position: bottom-right
4. Opacity: 50-70%
5. Apply to all

### Creating Thumbnails
1. Upload images
2. Resize to 300×300
3. Choose "Cover" fit mode
4. Download as batch

### Product Photo Editing
1. Upload product photos
2. Remove background (AI)
3. Add white background
4. Resize for marketplace
5. Export as PNG

---

## What's Next?

- [[Dashboard Overview]] - Full interface guide
- [[Image Editor]] - Advanced editing features
- [[AI Features]] - Background removal & more
- [[REST API]] - Automate with API

---

Enjoy using ImageMagick WebGUI! 🖼️
