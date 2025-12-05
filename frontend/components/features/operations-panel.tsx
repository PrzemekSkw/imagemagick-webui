'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  Play, 
  RotateCcw,
  RotateCw,
  FlipHorizontal,
  FlipVertical,
  Terminal,
  Loader2,
  Link2,
  Link2Off,
} from 'lucide-react';
import { useStore } from '@/lib/store';
import { operationsApi, imagesApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import Editor from '@monaco-editor/react';

export function OperationsPanel() {
  const { 
    activeCategory, 
    setActiveCategory,
    outputFormat,
    setOutputFormat,
    quality,
    setQuality,
    selectedImageIds,
    images,
  } = useStore();

  // Helper to get current valid selected IDs
  const getValidSelectedIds = () => {
    const state = useStore.getState();
    return state.selectedImageIds.filter(id => 
      state.images.some(img => img.id === id)
    );
  };

  // Get first selected image for aspect ratio calculation
  const getFirstSelectedImage = () => {
    const validIds = getValidSelectedIds();
    if (validIds.length === 0) return null;
    return images.find(img => img.id === validIds[0]);
  };

  const displaySelectedCount = selectedImageIds.filter(id => 
    images.some(img => img.id === id)
  ).length;

  // Resize state
  const [resizeMode, setResizeMode] = useState<'dimensions' | 'percent'>('dimensions');
  const [width, setWidth] = useState(800);
  const [height, setHeight] = useState(600);
  const [percent, setPercent] = useState(50);
  const [preserveAspect, setPreserveAspect] = useState(true);
  const [resizeFit, setResizeFit] = useState('fit');
  const [aspectRatio, setAspectRatio] = useState(1.333); // Default 4:3

  // Rotate state
  const [rotation, setRotation] = useState(0);

  // Watermark state
  const [watermarkText, setWatermarkText] = useState('');
  const [watermarkPosition, setWatermarkPosition] = useState('southeast');
  const [watermarkFontSize, setWatermarkFontSize] = useState(24);

  // Terminal state
  const [rawCommand, setRawCommand] = useState('');

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [commandPreview, setCommandPreview] = useState('');

  // Sync category to valid ones for dashboard
  useEffect(() => {
    const validCategories = ['resize', 'rotate', 'watermark', 'advanced'];
    if (!validCategories.includes(activeCategory)) {
      setActiveCategory('resize');
    }
  }, [activeCategory, setActiveCategory]);

  // Update aspect ratio when selection changes
  useEffect(() => {
    const img = getFirstSelectedImage();
    if (img && img.width && img.height) {
      const ratio = img.width / img.height;
      setAspectRatio(ratio);
      setWidth(img.width);
      setHeight(img.height);
    }
  }, [selectedImageIds, images]);

  // Handle width change with aspect ratio
  const handleWidthChange = useCallback((newWidth: number) => {
    setWidth(newWidth);
    if (preserveAspect && aspectRatio > 0) {
      setHeight(Math.round(newWidth / aspectRatio));
    }
  }, [preserveAspect, aspectRatio]);

  // Handle height change with aspect ratio
  const handleHeightChange = useCallback((newHeight: number) => {
    setHeight(newHeight);
    if (preserveAspect && aspectRatio > 0) {
      setWidth(Math.round(newHeight * aspectRatio));
    }
  }, [preserveAspect, aspectRatio]);

  // Build command preview
  useEffect(() => {
    const buildPreview = async () => {
      const ops: any[] = [];

      if (activeCategory === 'resize') {
        if (resizeMode === 'dimensions') {
          ops.push({
            operation: 'resize',
            params: { width, height, mode: resizeFit }
          });
        } else {
          ops.push({
            operation: 'resize',
            params: { percent }
          });
        }
      }

      if (activeCategory === 'rotate') {
        if (rotation !== 0) {
          ops.push({ operation: 'rotate', params: { angle: rotation } });
        }
      }

      if (activeCategory === 'watermark') {
        if (watermarkText) {
          ops.push({
            operation: 'watermark',
            params: {
              text: watermarkText,
              position: watermarkPosition,
              font_size: watermarkFontSize,
              opacity: 0.7
            }
          });
        }
      }

      if (activeCategory === 'advanced') {
        setCommandPreview(rawCommand || 'magick input.jpg [your options] output.jpg');
        return;
      }

      if (ops.length > 0) {
        try {
          const preview = await operationsApi.previewCommand(ops, outputFormat, quality);
          setCommandPreview(preview.command);
        } catch {
          setCommandPreview('Error building command');
        }
      } else {
        setCommandPreview('Select operations to see command preview');
      }
    };

    buildPreview();
  }, [activeCategory, width, height, percent, resizeMode, resizeFit, rotation, rawCommand, outputFormat, quality, watermarkText, watermarkPosition, watermarkFontSize]);

  // Refresh images helper
  const refreshImages = async () => {
    try {
      const imagesData = await imagesApi.list();
      const imagesList = Array.isArray(imagesData) ? imagesData : (imagesData.images || []);
      useStore.getState().setImages(imagesList.map((img: any) => ({
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
      })));
    } catch (e) {
      console.error('Failed to refresh images:', e);
    }
  };

  // Apply operations using SYNC endpoint for instant results
  const handleApply = async () => {
    const validIds = getValidSelectedIds();
    if (validIds.length === 0) {
      toast.error('No images selected');
      return;
    }

    setIsProcessing(true);

    try {
      const ops: any[] = [];

      if (activeCategory === 'resize') {
        if (resizeMode === 'dimensions') {
          ops.push({
            operation: 'resize',
            params: { width, height, mode: resizeFit }
          });
        } else {
          ops.push({
            operation: 'resize',
            params: { percent }
          });
        }
      }

      if (activeCategory === 'rotate') {
        if (rotation !== 0) {
          ops.push({ operation: 'rotate', params: { angle: rotation } });
        }
      }

      if (activeCategory === 'watermark') {
        if (watermarkText) {
          ops.push({
            operation: 'watermark',
            params: {
              text: watermarkText,
              position: watermarkPosition,
              font_size: watermarkFontSize,
              opacity: 0.7
            }
          });
        }
      }

      if (activeCategory === 'advanced') {
        if (!rawCommand.trim()) {
          toast.error('Enter a command first');
          setIsProcessing(false);
          return;
        }

        // For terminal mode, use async queue
        const result = await operationsApi.processRaw(validIds, rawCommand, outputFormat);
        toast.success('Job queued', { description: `Job ID: ${result.job_id}` });
        setTimeout(refreshImages, 2000);
        setIsProcessing(false);
        return;
      }

      if (ops.length === 0) {
        toast.error('No operations to apply');
        setIsProcessing(false);
        return;
      }

      // Process each image synchronously for instant feedback
      let successCount = 0;
      let errorCount = 0;

      for (const imageId of validIds) {
        try {
          await operationsApi.processSync(imageId, ops, outputFormat);
          successCount++;
        } catch (error: any) {
          console.error(`Failed to process image ${imageId}:`, error);
          errorCount++;
        }
      }

      if (successCount > 0) {
        toast.success(`Processed ${successCount} image(s)`, {
          description: errorCount > 0 ? `${errorCount} failed` : undefined
        });
      } else {
        toast.error('All operations failed');
      }

      // Refresh gallery
      await refreshImages();

    } catch (error: any) {
      toast.error('Processing failed', { description: error.message });
    } finally {
      setIsProcessing(false);
    }
  };

  // Quick rotate buttons
  const handleQuickRotate = async (angle: number) => {
    const validIds = getValidSelectedIds();
    if (validIds.length === 0) {
      toast.error('No images selected');
      return;
    }

    setIsProcessing(true);
    try {
      const ops = [{ operation: 'rotate', params: { angle } }];
      
      let successCount = 0;
      for (const imageId of validIds) {
        try {
          await operationsApi.processSync(imageId, ops, outputFormat);
          successCount++;
        } catch (e) {
          console.error(`Rotate failed for image ${imageId}:`, e);
        }
      }
      
      if (successCount > 0) {
        toast.success(`Rotated ${successCount} image(s) by ${angle}°`);
        await refreshImages();
      } else {
        toast.error('Rotation failed');
      }
    } catch (error: any) {
      toast.error('Rotation failed', { description: error.message });
    } finally {
      setIsProcessing(false);
    }
  };

  // Quick flip
  const handleFlip = async (direction: 'horizontal' | 'vertical') => {
    const validIds = getValidSelectedIds();
    if (validIds.length === 0) {
      toast.error('No images selected');
      return;
    }

    setIsProcessing(true);
    try {
      const ops = [{ operation: direction === 'horizontal' ? 'flop' : 'flip', params: {} }];
      
      let successCount = 0;
      for (const imageId of validIds) {
        try {
          await operationsApi.processSync(imageId, ops, outputFormat);
          successCount++;
        } catch (e) {
          console.error(`Flip failed for image ${imageId}:`, e);
        }
      }
      
      if (successCount > 0) {
        toast.success(`Flipped ${successCount} image(s) ${direction}`);
        await refreshImages();
      } else {
        toast.error('Flip failed');
      }
    } catch (error: any) {
      toast.error('Flip failed', { description: error.message });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <motion.div 
      className="h-full flex flex-col bg-white rounded-2xl shadow-sm border border-gray-100"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <h2 className="font-semibold text-gray-900">Quick Operations</h2>
        <p className="text-sm text-gray-500 mt-1">
          {displaySelectedCount > 0 
            ? `${displaySelectedCount} image(s) selected` 
            : 'Select images to process'}
        </p>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-4">
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="grid grid-cols-4 w-full mb-4">
            <TabsTrigger value="resize">Resize</TabsTrigger>
            <TabsTrigger value="rotate">Rotate</TabsTrigger>
            <TabsTrigger value="watermark">Text</TabsTrigger>
            <TabsTrigger value="advanced">Terminal</TabsTrigger>
          </TabsList>

          {/* Resize Tab */}
          <TabsContent value="resize" className="space-y-4 mt-4">
            <Tabs value={resizeMode} onValueChange={(v) => setResizeMode(v as any)}>
              <TabsList className="w-full">
                <TabsTrigger value="dimensions" className="flex-1">Dimensions</TabsTrigger>
                <TabsTrigger value="percent" className="flex-1">Percentage</TabsTrigger>
              </TabsList>

              <TabsContent value="dimensions" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-gray-500">Width</Label>
                    <Input
                      type="number"
                      value={width}
                      onChange={(e) => handleWidthChange(Number(e.target.value))}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-gray-500">Height</Label>
                    <Input
                      type="number"
                      value={height}
                      onChange={(e) => handleHeightChange(Number(e.target.value))}
                      className="mt-1"
                    />
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPreserveAspect(!preserveAspect)}
                  className="w-full flex items-center justify-center gap-2"
                >
                  {preserveAspect ? (
                    <>
                      <Link2 className="h-4 w-4" />
                      Aspect Ratio Locked
                    </>
                  ) : (
                    <>
                      <Link2Off className="h-4 w-4" />
                      Aspect Ratio Unlocked
                    </>
                  )}
                </Button>

                <div>
                  <Label className="text-xs text-gray-500">Fit Mode</Label>
                  <Select value={resizeFit} onValueChange={setResizeFit}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fit">Fit (within bounds)</SelectItem>
                      <SelectItem value="fill">Fill (cover bounds)</SelectItem>
                      <SelectItem value="force">Force (exact size)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Quick presets */}
                <div>
                  <Label className="text-xs text-gray-500 mb-2 block">Quick Presets</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { label: 'HD', w: 1280, h: 720 },
                      { label: 'Full HD', w: 1920, h: 1080 },
                      { label: '4K', w: 3840, h: 2160 },
                      { label: 'Square', w: 1080, h: 1080 },
                    ].map((preset) => (
                      <Button
                        key={preset.label}
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setPreserveAspect(false);
                          setWidth(preset.w);
                          setHeight(preset.h);
                          setAspectRatio(preset.w / preset.h);
                        }}
                      >
                        {preset.label}
                      </Button>
                    ))}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="percent" className="space-y-4 mt-4">
                <div>
                  <Label className="text-xs text-gray-500">Scale: {percent}%</Label>
                  <Slider
                    value={[percent]}
                    onValueChange={([v]) => setPercent(v)}
                    min={10}
                    max={200}
                    step={5}
                    className="mt-2"
                  />
                </div>

                <div className="grid grid-cols-3 gap-2">
                  {[25, 50, 75, 100, 150, 200].map((p) => (
                    <Button
                      key={p}
                      variant={percent === p ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setPercent(p)}
                    >
                      {p}%
                    </Button>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </TabsContent>

          {/* Rotate Tab */}
          <TabsContent value="rotate" className="space-y-4 mt-4">
            <div>
              <Label className="text-xs text-gray-500">Rotation: {rotation}°</Label>
              <Slider
                value={[rotation]}
                onValueChange={([v]) => setRotation(v)}
                min={-180}
                max={180}
                step={1}
                className="mt-2"
              />
            </div>

            <div className="grid grid-cols-4 gap-2">
              <Button variant="outline" size="sm" onClick={() => handleQuickRotate(-90)} disabled={isProcessing}>
                <RotateCcw className="h-4 w-4 mr-1" /> -90°
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleQuickRotate(90)} disabled={isProcessing}>
                <RotateCw className="h-4 w-4 mr-1" /> +90°
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleQuickRotate(180)} disabled={isProcessing}>
                180°
              </Button>
              <Button variant="outline" size="sm" onClick={() => setRotation(0)}>
                Reset
              </Button>
            </div>

            <div className="pt-2 border-t">
              <Label className="text-xs text-gray-500 mb-2 block">Flip</Label>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="outline" size="sm" onClick={() => handleFlip('horizontal')} disabled={isProcessing}>
                  <FlipHorizontal className="h-4 w-4 mr-1" /> Horizontal
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleFlip('vertical')} disabled={isProcessing}>
                  <FlipVertical className="h-4 w-4 mr-1" /> Vertical
                </Button>
              </div>
            </div>
          </TabsContent>

          {/* Watermark/Text Tab */}
          <TabsContent value="watermark" className="space-y-4 mt-4">
            <div>
              <Label className="text-xs text-gray-500">Text</Label>
              <Input
                value={watermarkText}
                onChange={(e) => setWatermarkText(e.target.value)}
                placeholder="Enter watermark text..."
                className="mt-1"
              />
            </div>

            <div>
              <Label className="text-xs text-gray-500">Position</Label>
              <div className="grid grid-cols-3 gap-1 mt-2 p-2 bg-gray-50 rounded-lg">
                {['northwest', 'north', 'northeast', 'west', 'center', 'east', 'southwest', 'south', 'southeast'].map((pos) => (
                  <Button
                    key={pos}
                    variant={watermarkPosition === pos ? 'default' : 'ghost'}
                    size="sm"
                    className="h-8 text-xs"
                    onClick={() => setWatermarkPosition(pos)}
                  >
                    {pos.replace('north', '↑').replace('south', '↓').replace('east', '→').replace('west', '←').replace('center', '•')}
                  </Button>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-xs text-gray-500">Font Size: {watermarkFontSize}pt</Label>
              <Slider
                value={[watermarkFontSize]}
                onValueChange={([v]) => setWatermarkFontSize(v)}
                min={8}
                max={72}
                step={2}
                className="mt-2"
              />
              <div className="flex gap-1 mt-2">
                {[12, 18, 24, 36, 48].map((size) => (
                  <Button
                    key={size}
                    variant={watermarkFontSize === size ? 'default' : 'outline'}
                    size="sm"
                    className="flex-1 text-xs"
                    onClick={() => setWatermarkFontSize(size)}
                  >
                    {size}
                  </Button>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Terminal Tab */}
          <TabsContent value="advanced" className="space-y-4 mt-4">
            <div className="rounded-lg overflow-hidden border border-gray-200">
              <div className="bg-gray-900 text-white px-3 py-2 text-xs flex items-center gap-2">
                <Terminal className="h-3 w-3" />
                <span>ImageMagick Terminal</span>
              </div>
              <Editor
                height="200px"
                defaultLanguage="shell"
                theme="vs-dark"
                value={rawCommand}
                onChange={(v) => setRawCommand(v || '')}
                options={{
                  minimap: { enabled: false },
                  lineNumbers: 'off',
                  fontSize: 13,
                  wordWrap: 'on',
                  scrollBeyondLastLine: false,
                }}
              />
            </div>

            <div className="text-xs text-gray-500 space-y-1">
              <p>Use <code className="bg-gray-100 px-1 rounded">%input%</code> for input file</p>
              <p>Use <code className="bg-gray-100 px-1 rounded">%output%</code> for output file</p>
              <p className="text-amber-600">⚠️ Some commands are blocked for security</p>
            </div>

            <div className="space-y-2">
              <Label className="text-xs text-gray-500">Quick Commands</Label>
              <div className="grid grid-cols-1 gap-1">
                {[
                  { label: 'Grayscale', cmd: '-colorspace Gray' },
                  { label: 'Sepia', cmd: '-sepia-tone 80%' },
                  { label: 'Negate', cmd: '-negate' },
                  { label: 'Auto-enhance', cmd: '-enhance -normalize' },
                ].map((item) => (
                  <Button
                    key={item.label}
                    variant="outline"
                    size="sm"
                    className="justify-start text-xs"
                    onClick={() => setRawCommand(item.cmd)}
                  >
                    {item.label}: <code className="ml-1 text-gray-500">{item.cmd}</code>
                  </Button>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Output Format */}
          <div className="mt-6 pt-4 border-t border-gray-100 space-y-4">
            <div>
              <Label className="text-xs text-gray-500">Output Format</Label>
              <Select value={outputFormat} onValueChange={setOutputFormat}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="webp">WebP (recommended)</SelectItem>
                  <SelectItem value="jpg">JPEG</SelectItem>
                  <SelectItem value="png">PNG</SelectItem>
                  <SelectItem value="avif">AVIF</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {outputFormat !== 'png' && (
              <div>
                <Label className="text-xs text-gray-500">Quality: {quality}%</Label>
                <Slider
                  value={[quality]}
                  onValueChange={([v]) => setQuality(v)}
                  min={1}
                  max={100}
                  step={1}
                  className="mt-2"
                />
              </div>
            )}
          </div>

          {/* Command Preview */}
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <Label className="text-xs text-gray-500 mb-1 block">Command Preview</Label>
            <code className="text-xs text-gray-700 break-all block">{commandPreview}</code>
          </div>
        </Tabs>
      </ScrollArea>

      {/* Actions - only Apply button, no duplicate Download/Delete */}
      <div className="p-4 border-t border-gray-100">
        <Button 
          className="w-full" 
          onClick={handleApply}
          disabled={isProcessing || displaySelectedCount === 0}
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Apply to {displaySelectedCount} image(s)
            </>
          )}
        </Button>
      </div>
    </motion.div>
  );
}
