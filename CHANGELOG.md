# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-05

### Added

- 🎉 Initial release of ImageMagick WebGUI
- **Image Upload**
  - Drag & drop multi-file upload
  - Support for JPEG, PNG, WebP, GIF, TIFF, BMP, SVG, PDF, AVIF
  - Automatic thumbnail generation
  - File size and MIME type validation

- **Image Processing**
  - Resize with dimensions or percentage
  - Aspect ratio preservation
  - Interactive crop tool
  - Rotate (90°, 180°, 270°) and flip (horizontal/vertical)
  - Format conversion between all supported formats
  - Quality control for lossy formats

- **Filters & Effects**
  - Blur with adjustable intensity
  - Sharpen
  - Grayscale conversion
  - Sepia tone
  - Brightness, contrast, saturation adjustments
  - Auto enhance with normalize + sharpen

- **Watermark**
  - Text watermark with custom content
  - 9-position placement grid
  - Adjustable font size (8-72pt)
  - Opacity control (10-100%)

- **AI Features**
  - Background removal using rembg with alpha matting
  - Image upscaling (2x, 4x) with LANCZOS algorithm
  - AI service status diagnostics

- **User Interface**
  - Modern, clean design inspired by Notion
  - Real-time preview for all adjustments
  - Command preview showing exact ImageMagick command
  - Dark/Light mode with system detection
  - Responsive design for mobile and tablet
  - PWA support for app installation

- **Editor**
  - Full-featured image editor modal
  - Live preview of all changes
  - Tabbed interface for organized controls
  - Quick action buttons (Enhance, Remove BG, Upscale)
  - Editable filename in header

- **Dashboard**
  - Quick operations panel
  - Batch processing for multiple images
  - Terminal mode for raw ImageMagick commands
  - Monaco editor for command input

- **Backend**
  - FastAPI with async support
  - PostgreSQL database
  - Redis job queue
  - Secure ImageMagick execution with resource limits
  - JWT authentication
  - Rate limiting

- **Security**
  - Sandboxed command execution
  - File type validation
  - Size limits
  - Timeout protection
  - Memory limits for ImageMagick

- **DevOps**
  - Docker multi-stage build
  - Docker Compose setup
  - Health checks
  - Auto cleanup of temporary files

### Security

- ImageMagick runs with 2GB memory limit
- 60-second timeout per operation
- Whitelisted operations only
- No shell injection possible

---

## [Unreleased]

### Planned

- [ ] Batch rename functionality
- [ ] Image comparison (before/after slider)
- [ ] Preset saving and loading
- [ ] Folder/album organization
- [ ] EXIF data viewing and editing
- [ ] Image metadata preservation options
- [ ] Webhook notifications
- [ ] S3/cloud storage integration
- [ ] Multi-user workspace support
