'use client';

import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Check, 
  Trash2, 
  Download, 
  Info, 
  Edit3,
  X,
  ImageIcon,
  FileText,
  FolderPlus,
  FolderMinus
} from 'lucide-react';
import { cn, formatFileSize } from '@/lib/utils';
import { useStore, ImageFile } from '@/lib/store';
import { imagesApi, projectsApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { ImageEditor } from './image-editor';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ImageCardProps {
  image: ImageFile;
  selected: boolean;
  onToggle: () => void;
  onDelete: () => void;
  onPreview: () => void;
  onEdit: () => void;
}

function ImageCard({ image, selected, onToggle, onDelete, onPreview, onEdit }: ImageCardProps) {
  const [imgError, setImgError] = useState(false);
  const [useFallback, setUseFallback] = useState(false);
  
  // Check if it's a PDF
  const isPdf = image.mimeType === 'application/pdf' || image.originalFilename.toLowerCase().endsWith('.pdf');
  
  // Try thumbnail first, fall back to full image
  const thumbnailUrl = `${API_URL}/api/images/${image.id}/thumbnail`;
  const fallbackUrl = `${API_URL}/api/images/${image.id}`;
  
  // Use fallback if thumbnail failed
  const currentUrl = useFallback ? fallbackUrl : thumbnailUrl;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={cn('image-thumbnail group', selected && 'selected')}
    >
      {/* Thumbnail or PDF icon */}
      {isPdf ? (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 dark:bg-red-950">
          <FileText className="h-12 w-12 text-red-500" />
        </div>
      ) : !imgError ? (
        <img
          src={currentUrl}
          alt={image.originalFilename}
          className="absolute inset-0 h-full w-full object-cover" style={{ backgroundImage: "linear-gradient(45deg, #e0e0e0 25%, transparent 25%), linear-gradient(-45deg, #e0e0e0 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #e0e0e0 75%), linear-gradient(-45deg, transparent 75%, #e0e0e0 75%)", backgroundSize: "16px 16px", backgroundPosition: "0 0, 0 8px, 8px -8px, -8px 0px" }}
          loading="lazy"
          onError={() => {
            if (!useFallback) {
              // Try fallback URL (full image)
              setUseFallback(true);
            } else {
              // Both failed, show icon
              setImgError(true);
            }
          }}
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center bg-secondary">
          <ImageIcon className="h-8 w-8 text-muted-foreground" />
        </div>
      )}

      {/* Overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Checkbox - click to toggle selection */}
      <div className="absolute top-2 left-2 z-10">
        <div 
          className={cn(
            'flex h-6 w-6 items-center justify-center rounded-md transition-all cursor-pointer',
            selected ? 'bg-primary' : 'bg-black/40 opacity-0 group-hover:opacity-100'
          )}
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
        >
          {selected && <Check className="h-4 w-4 text-primary-foreground" />}
        </div>
      </div>

      {/* Actions */}
      <div className="absolute top-2 right-2 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="secondary"
          size="icon"
          className="h-7 w-7 bg-black/40 hover:bg-primary text-white"
          onClick={(e) => {
            e.stopPropagation();
            onEdit();
          }}
          title="Edit"
        >
          <Edit3 className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="secondary"
          size="icon"
          className="h-7 w-7 bg-black/40 hover:bg-black/60 text-white"
          onClick={(e) => {
            e.stopPropagation();
            onPreview();
          }}
          title="Info"
        >
          <Info className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="secondary"
          size="icon"
          className="h-7 w-7 bg-black/40 hover:bg-destructive text-white"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          title="Delete"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Click to edit */}
      <div 
        className="absolute inset-0 cursor-pointer z-0"
        onDoubleClick={(e) => {
          e.stopPropagation();
          onEdit();
        }}
        onClick={(e) => {
          e.stopPropagation();
          onToggle();
        }}
      />

      {/* Info */}
      <div className="absolute bottom-0 left-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        <p className="text-xs text-white font-medium truncate">
          {image.originalFilename}
        </p>
        <p className="text-xs text-white/70">
          {formatFileSize(image.fileSize)}
          {image.width && image.height && ` • ${image.width}×${image.height}`}
        </p>
      </div>
    </motion.div>
  );
}

export function ImageGallery() {
  const { 
    images, 
    setImages, 
    selectedImageIds, 
    toggleImageSelection, 
    removeImage, 
    removeImages,
    selectImages,
    clearSelection, 
    activeProjectId, 
    token,
    projects,
    setProjects
  } = useStore();
  
  const [previewImage, setPreviewImage] = useState<ImageFile | null>(null);
  const [editingImage, setEditingImage] = useState<ImageFile | null>(null);
  const [showAddToProjectDialog, setShowAddToProjectDialog] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');

  // Filter images by project
  const filteredImages = activeProjectId 
    ? images.filter(img => img.projectId === activeProjectId)
    : images;

  // Helper to get current valid selected IDs from fresh state (call inside handlers)
  const getValidSelectedIds = () => {
    const state = useStore.getState();
    const currentFiltered = state.activeProjectId 
      ? state.images.filter(img => img.projectId === state.activeProjectId)
      : state.images;
    return state.selectedImageIds.filter(id => 
      currentFiltered.some(img => img.id === id)
    );
  };

  // For display purposes (computed at render time)
  const displaySelectedCount = selectedImageIds.filter(id => 
    filteredImages.some(img => img.id === id)
  ).length;

  // Refresh images from API
  const refreshImages = useCallback(async () => {
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
      console.error('Failed to refresh images:', error);
    }
  }, [setImages]);

  // Refresh project counts
  const refreshProjects = useCallback(async () => {
    if (!token) return;
    try {
      const data = await projectsApi.list();
      setProjects(data.projects || []);
    } catch (error) {
      console.error('Failed to refresh projects:', error);
    }
  }, [token, setProjects]);

  // Add selected images to project
  const handleAddToProject = async () => {
    const validIds = getValidSelectedIds();
    if (!selectedProjectId || validIds.length === 0) return;

    try {
      await projectsApi.addImages(parseInt(selectedProjectId), validIds);
      toast.success(`Added ${validIds.length} image(s) to project`);
      setShowAddToProjectDialog(false);
      setSelectedProjectId('');
      clearSelection();
      await refreshImages();
      await refreshProjects();
    } catch (error) {
      toast.error('Failed to add images to project');
    }
  };

  // Remove selected images from project
  const handleRemoveFromProject = async () => {
    const validIds = getValidSelectedIds();
    if (validIds.length === 0) return;

    try {
      await projectsApi.removeImages(validIds);
      toast.success(`Removed ${validIds.length} image(s) from project`);
      clearSelection();
      await refreshImages();
      await refreshProjects();
    } catch (error) {
      toast.error('Failed to remove images from project');
    }
  };

  const handleDelete = async (image: ImageFile) => {
    try {
      await imagesApi.delete(image.id);
      removeImage(image.id);
      await refreshProjects();
      toast.success('Image deleted');
    } catch (error) {
      toast.error('Failed to delete image');
    }
  };

  const handleDownloadSelected = async () => {
    const validIds = getValidSelectedIds();
    if (validIds.length === 0) return;
    
    try {
      // If single image, download directly
      if (validIds.length === 1) {
        const imageId = validIds[0];
        const image = images.find(img => img.id === imageId);
        const response = await fetch(`${API_URL}/api/images/${imageId}`);
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = image?.originalFilename || `image_${imageId}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // Multiple images - download as ZIP
        const blob = await imagesApi.downloadZip(validIds);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'images.zip';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
      toast.success('Download started');
    } catch (error) {
      toast.error('Failed to download images');
    }
  };

  const handleDeleteSelected = async () => {
    const validIds = getValidSelectedIds();
    if (validIds.length === 0) return;
    
    const count = validIds.length;
    if (!confirm(`Are you sure you want to delete ${count} image${count > 1 ? 's' : ''}?`)) {
      return;
    }
    
    try {
      // Delete all selected images - use the exact IDs we're about to delete
      const idsToDelete = [...validIds];
      await Promise.all(idsToDelete.map(id => imagesApi.delete(id)));
      
      // Remove from store using batch operation
      removeImages(idsToDelete);
      
      // Update project counts
      await refreshProjects();
      
      toast.success(`Deleted ${count} image${count > 1 ? 's' : ''}`);
    } catch (error) {
      toast.error('Failed to delete some images');
      // Refresh to get current state
      await refreshImages();
    }
  };

  // Called when editor closes - refresh gallery to show new copies
  const handleEditorClose = useCallback(() => {
    setEditingImage(null);
    refreshImages();
  }, [refreshImages]);

  // Show empty state if no images at all
  if (images.length === 0) {
    return null;
  }

  // Show message if project is selected but has no images
  if (activeProjectId && filteredImages.length === 0) {
    return (
      <div className="text-center py-12">
        <FolderMinus className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
        <p className="text-muted-foreground">No images in this project</p>
        <p className="text-sm text-muted-foreground/70 mt-1">
          Select images from "All Images" and add them to this project
        </p>
      </div>
    );
  }

  // Select all filtered images (only visible ones)
  const selectAllFiltered = () => {
    const filteredIds = filteredImages.map(img => img.id);
    selectImages(filteredIds);
  };

  // Check if all filtered images are selected
  const allFilteredSelected = filteredImages.length > 0 && 
    filteredImages.every(img => selectedImageIds.includes(img.id));

  return (
    <>
      <div className="space-y-4">
        {/* Toolbar - responsive with wrapping */}
        <div className="space-y-3">
          {/* Selection controls row */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={selectAllFiltered}
              disabled={allFilteredSelected || filteredImages.length === 0}
            >
              Select All{activeProjectId ? ' in Project' : ''}
            </Button>
            {displaySelectedCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSelection}
              >
                Clear
              </Button>
            )}
            <span className="text-sm text-muted-foreground whitespace-nowrap">
              {displaySelectedCount > 0 ? `${displaySelectedCount} selected` : ''}
              {activeProjectId && ` • ${filteredImages.length} in project`}
            </span>
          </div>
          
          {/* Action buttons row - only show when images selected */}
          {displaySelectedCount > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              {token && projects.length > 0 && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddToProjectDialog(true)}
                    className="gap-1.5"
                  >
                    <FolderPlus className="h-4 w-4" />
                    <span className="hidden sm:inline">Add to Project</span>
                    <span className="sm:hidden">Project</span>
                  </Button>
                  {activeProjectId && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleRemoveFromProject}
                      className="gap-1.5"
                    >
                      <FolderMinus className="h-4 w-4" />
                      <span className="hidden sm:inline">Remove</span>
                    </Button>
                  )}
                </>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadSelected}
                className="gap-1.5"
              >
                <Download className="h-4 w-4" />
                <span className="hidden sm:inline">Download</span>
                {displaySelectedCount > 1 && <span className="text-xs">({displaySelectedCount})</span>}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDeleteSelected}
                className="gap-1.5 text-destructive hover:bg-destructive hover:text-destructive-foreground"
              >
                <Trash2 className="h-4 w-4" />
                <span className="hidden sm:inline">Delete</span>
                {displaySelectedCount > 1 && <span className="text-xs">({displaySelectedCount})</span>}
              </Button>
            </div>
          )}
        </div>

        {/* Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          <AnimatePresence>
            {filteredImages.map((image) => (
              <ImageCard
                key={image.id}
                image={image}
                selected={selectedImageIds.includes(image.id)}
                onToggle={() => toggleImageSelection(image.id)}
                onDelete={() => handleDelete(image)}
                onPreview={() => setPreviewImage(image)}
                onEdit={() => setEditingImage(image)}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* Preview Dialog */}
        <Dialog open={!!previewImage} onOpenChange={() => setPreviewImage(null)}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle className="truncate pr-8">
                {previewImage?.originalFilename}
              </DialogTitle>
            </DialogHeader>
            
            {previewImage && (
              <div className="space-y-4">
                <div className="relative aspect-video rounded-xl overflow-hidden" style={{ backgroundImage: "linear-gradient(45deg, #e5e5e5 25%, transparent 25%), linear-gradient(-45deg, #e5e5e5 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #e5e5e5 75%), linear-gradient(-45deg, transparent 75%, #e5e5e5 75%)", backgroundSize: "16px 16px", backgroundPosition: "0 0, 0 8px, 8px -8px, -8px 0px", backgroundColor: "white" }}>
                  {previewImage.mimeType === 'application/pdf' ? (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <FileText className="h-24 w-24 text-red-500" />
                    </div>
                  ) : (
                    <img
                      src={`${API_URL}/api/images/${previewImage.id}`}
                      alt={previewImage.originalFilename}
                      className="absolute inset-0 h-full w-full object-contain"
                    />
                  )}
                </div>
                
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Format</p>
                    <p className="font-medium">{previewImage.format || 'Unknown'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Size</p>
                    <p className="font-medium">{formatFileSize(previewImage.fileSize)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Dimensions</p>
                    <p className="font-medium">
                      {previewImage.width && previewImage.height 
                        ? `${previewImage.width} × ${previewImage.height}` 
                        : 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Type</p>
                    <p className="font-medium">{previewImage.mimeType}</p>
                  </div>
                </div>
                
                <div className="flex gap-2 justify-end">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setPreviewImage(null);
                      setEditingImage(previewImage);
                    }}
                  >
                    <Edit3 className="h-4 w-4 mr-2" />
                    Edit Image
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>

      {/* Image Editor Modal */}
      {editingImage && (
        <ImageEditor
          image={editingImage}
          onClose={handleEditorClose}
          onSave={handleEditorClose}
        />
      )}

      {/* Add to Project Dialog */}
      <Dialog open={showAddToProjectDialog} onOpenChange={setShowAddToProjectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add to Project</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a project..." />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id.toString()}>
                    <div className="flex items-center gap-2">
                      <div 
                        className="h-3 w-3 rounded" 
                        style={{ backgroundColor: project.color }}
                      />
                      {project.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddToProjectDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddToProject} disabled={!selectedProjectId || displaySelectedCount === 0}>
              Add {displaySelectedCount} image{displaySelectedCount !== 1 ? 's' : ''}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
