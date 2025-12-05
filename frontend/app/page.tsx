'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { UploadZone } from '@/components/features/upload-zone';
import { ImageGallery } from '@/components/features/image-gallery';
import { OperationsPanel } from '@/components/features/operations-panel';
import { useStore } from '@/lib/store';
import { imagesApi, authApi } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';

export default function HomePage() {
  const { images, setImages, token, setUser, sidebarOpen } = useStore();

  // Load user data on mount
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const userData = await authApi.me();
          setUser(userData);
        } catch (error) {
          // Token invalid, clear it
          useStore.getState().logout();
        }
      }
    };
    loadUser();
  }, [token, setUser]);

  // Load images on mount
  useEffect(() => {
    const loadImages = async () => {
      try {
        const data = await imagesApi.list();
        // Handle both array and object with images property
        const imagesList = Array.isArray(data) ? data : (data.images || []);
        const formattedImages = imagesList.map((img: any) => ({
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
          projectId: img.project_id,
        }));
        setImages(formattedImages);
      } catch (error) {
        console.error('Failed to load images:', error);
      }
    };
    loadImages();
  }, [setImages]);

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header />

        <div className="flex-1 flex min-h-0">
          {/* Left: Gallery */}
          <ScrollArea className="flex-1 p-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="space-y-6 max-w-6xl mx-auto"
            >
              {/* Upload Zone */}
              <UploadZone />

              {/* Gallery */}
              <ImageGallery />
            </motion.div>
          </ScrollArea>

          {/* Right: Operations Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="w-[380px] border-l border-border hidden lg:block"
          >
            <OperationsPanel />
          </motion.div>
        </div>
      </div>

      {/* Mobile operations panel as drawer */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-background border-t border-border p-4">
        <div className="text-center text-sm text-muted-foreground">
          Open on desktop for full editing experience
        </div>
      </div>
    </div>
  );
}
