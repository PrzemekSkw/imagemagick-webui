# Batch Processing

Process multiple images simultaneously with the same operations.

---

## Overview

Batch processing allows you to:
- Apply identical operations to multiple images
- Save time on repetitive tasks
- Maintain consistency across image sets
- Download all results as a ZIP archive

---

## How to Batch Process

### Step 1: Upload Images

Upload multiple images at once:
- **Drag & drop** multiple files onto the upload zone
- **Click upload** and select multiple files (Ctrl+Click)

### Step 2: Select Images

Select images to process:
- **Click** individual thumbnails
- **Ctrl + Click** to add/remove from selection
- **Shift + Click** to select a range
- **"Select All"** button for everything

### Step 3: Choose Operation

In the Quick Operations panel:
1. Select a tab (Resize, Rotate, Text, Terminal)
2. Configure the operation settings
3. Preview the command

### Step 4: Apply

Click **"Apply to X image(s)"** button.

### Step 5: Download Results

After processing:
- New images appear in the gallery
- Click **"Download as ZIP"** for bulk download

---

## Batch Operations

### Resize All

```
Example: Resize 50 product photos to 800x600

1. Upload all 50 images
2. Select All
3. Resize tab → 800 × 600, Preserve Aspect Ratio
4. Apply to 50 image(s)
5. Download as ZIP
```

### Add Watermark

```
Example: Add copyright to portfolio

1. Select portfolio images
2. Text tab → "© 2024 Your Name"
3. Position: Southeast
4. Font Size: 24pt
5. Apply
```

### Convert Format

```
Example: Convert PNG to WebP for web

1. Select PNG images
2. Terminal tab
3. Output Format: WebP
4. Quality: 80%
5. Apply
```

### Create Thumbnails

```
Example: Generate 300x300 thumbnails

1. Select images
2. Resize tab → 300 × 300
3. Fit Mode: Cover
4. Apply
```

---

## Queue System

For large batches, operations are queued:

```
┌─────────────────────────────────────────┐
│  Processing Queue                       │
├─────────────────────────────────────────┤
│  ✓ image_001.jpg    Complete            │
│  ✓ image_002.jpg    Complete            │
│  ⟳ image_003.jpg    Processing...       │
│  ○ image_004.jpg    Queued              │
│  ○ image_005.jpg    Queued              │
├─────────────────────────────────────────┤
│  Progress: 2/5 (40%)  ████░░░░░░        │
└─────────────────────────────────────────┘
```

### Queue Features

- **Real-time progress** - See each image status
- **Background processing** - Continue using the app
- **Cancel option** - Stop processing at any time
- **Error handling** - Failed images shown with reason

---

## Performance Tips

### Optimize Batch Size

| Images | Processing | Recommendation |
|--------|------------|----------------|
| 1-10 | Instant | Direct processing |
| 10-50 | Fast | Queue recommended |
| 50-100 | Moderate | Use queue |
| 100+ | Slow | Split into batches |

### Best Practices

1. **Similar sizes first** - Group images by size for faster processing
2. **Reduce before converting** - Resize before format conversion saves time
3. **Use WebP** - Smaller files, faster processing
4. **Check one first** - Test settings on single image before batch

### Memory Management

- Large batches use significant memory
- System limits: 2GB per operation
- Very large images may timeout

---

## Batch Workflows

### E-commerce Product Photos

```
1. Upload raw product photos
2. Resize to 1200×1200 (Cover mode)
3. Apply → Download ZIP
4. Re-select originals
5. Resize to 400×400 (thumbnails)
6. Apply → Download ZIP
```

### Social Media Optimization

```
Platform sizes:
- Instagram: 1080×1080 (Cover)
- Facebook: 1200×630 (Cover)
- Twitter: 1600×900 (Cover)

Process same images 3 times with different sizes
```

### Web Gallery Preparation

```
1. Upload high-res originals
2. Batch resize to 1920×1080 (Contain)
3. Convert to WebP, quality 85%
4. Add watermark
5. Download ZIP for upload
```

---

## Troubleshooting

### Batch Stuck

1. Check browser console (F12) for errors
2. Refresh page and retry
3. Reduce batch size

### Some Images Failed

1. Check file format is supported
2. Verify file isn't corrupted
3. Try processing failed images individually

### Slow Processing

1. Use smaller image dimensions
2. Reduce batch size
3. Close other browser tabs
4. Check server resources

---

## Limits

| Limit | Value |
|-------|-------|
| Max files per upload | 100 |
| Max file size | 50MB |
| Max batch size | 100 images |
| Processing timeout | 60 seconds/image |
| Memory per operation | 2GB |

---

## Next Steps

- [[Dashboard Overview]] - Main interface
- [[Terminal Mode]] - Advanced batch commands
- [[Format Conversion]] - Output format options
