'use client';

import { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Image, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useStore } from '@/lib/store';
import { imagesApi } from '@/lib/api';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';

const ACCEPTED_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/webp': ['.webp'],
  'image/gif': ['.gif'],
  'image/svg+xml': ['.svg'],
  'image/tiff': ['.tiff', '.tif'],
  'application/pdf': ['.pdf'],
  'image/bmp': ['.bmp'],
  'image/heic': ['.heic'],
  'image/heif': ['.heif'],
  'image/avif': ['.avif'],
};

export function UploadZone() {
  const { addImages } = useStore();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  // Prevent browser from opening files when dropped outside the dropzone
  useEffect(() => {
    const preventDefaults = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
    };

    // Add listeners to window to prevent default behavior everywhere
    window.addEventListener('dragenter', preventDefaults);
    window.addEventListener('dragover', preventDefaults);
    window.addEventListener('dragleave', preventDefaults);
    window.addEventListener('drop', preventDefaults);

    return () => {
      window.removeEventListener('dragenter', preventDefaults);
      window.removeEventListener('dragover', preventDefaults);
      window.removeEventListener('dragleave', preventDefaults);
      window.removeEventListener('drop', preventDefaults);
    };
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setProgress(0);

    try {
      const response = await imagesApi.upload(acceptedFiles, (p) => setProgress(p));
      
      if (response.images.length > 0) {
        const formattedImages = response.images.map((img: any) => ({
          id: img.id,
          originalFilename: img.original_filename,
          storedFilename: img.stored_filename,
          thumbnailUrl: img.thumbnail_url,
          mimeType: img.mime_type,
          fileSize: img.file_size,
          width: img.width,
          height: img.height,
          format: img.format,
          createdAt: img.created_at,
        }));
        
        addImages(formattedImages);
        toast.success(`Uploaded ${response.images.length} image(s)`);
      }

      if (response.failed.length > 0) {
        toast.error(`Failed to upload ${response.failed.length} file(s)`);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [addImages]);

  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: 100 * 1024 * 1024, // 100MB
    disabled: uploading,
    noClick: false,
    noKeyboard: false,
    preventDropOnDocument: true,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        'upload-zone',
        isDragActive && 'dragging',
        isDragReject && 'border-destructive bg-destructive/5',
        uploading && 'pointer-events-none opacity-70'
      )}
    >
      <input {...getInputProps()} />
      
      <div className="flex flex-col items-center justify-center text-center">
        <AnimatePresence mode="wait">
          {uploading ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-4"
            >
              <Loader2 className="h-12 w-12 text-primary animate-spin" />
              <div className="space-y-2 w-48">
                <p className="text-sm font-medium">Uploading...</p>
                <Progress value={progress} className="h-1.5" />
                <p className="text-xs text-muted-foreground">{progress}%</p>
              </div>
            </motion.div>
          ) : isDragReject ? (
            <motion.div
              key="reject"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-3"
            >
              <XCircle className="h-12 w-12 text-destructive" />
              <p className="text-sm font-medium text-destructive">
                Invalid file type
              </p>
            </motion.div>
          ) : isDragActive ? (
            <motion.div
              key="active"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-3"
            >
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 0.6, repeat: Infinity }}
              >
                <Upload className="h-12 w-12 text-primary" />
              </motion.div>
              <p className="text-sm font-medium">Drop files here</p>
            </motion.div>
          ) : (
            <motion.div
              key="default"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-3"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary">
                <Image className="h-8 w-8 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">
                  Drop images here or click to browse
                </p>
                <p className="text-xs text-muted-foreground">
                  Supports JPG, PNG, WebP, GIF, SVG, TIFF, PDF, and more
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
