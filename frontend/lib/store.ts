import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ImageFile {
  id: number;
  originalFilename: string;
  storedFilename: string;
  thumbnailUrl: string | null;
  mimeType: string;
  fileSize: number;
  width: number | null;
  height: number | null;
  format: string | null;
  createdAt: string;
  projectId: number | null;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  color: string;
  icon: string;
  image_count: number;
}

export interface Operation {
  operation: string;
  params: Record<string, any>;
}

export interface Job {
  id: number;
  jobId: string;
  operation: string;
  status: string;
  progress: number;
  errorMessage: string | null;
  inputFiles: number[];
  outputFiles: string[];
  createdAt: string;
  startedAt: string | null;
  completedAt: string | null;
}

interface User {
  id: number;
  email: string;
  name: string | null;
  is_admin?: boolean;
}

interface AppState {
  // User
  user: User | null;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
  
  // Images
  images: ImageFile[];
  selectedImageIds: number[];
  setImages: (images: ImageFile[]) => void;
  addImages: (images: ImageFile[]) => void;
  removeImage: (id: number) => void;
  removeImages: (ids: number[]) => void;
  toggleImageSelection: (id: number) => void;
  selectAllImages: () => void;
  selectImages: (ids: number[]) => void;
  clearSelection: () => void;
  
  // Projects
  projects: Project[];
  activeProjectId: number | null;
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  updateProject: (id: number, updates: Partial<Project>) => void;
  removeProject: (id: number) => void;
  setActiveProjectId: (projectId: number | null) => void;
  
  // Operations
  operations: Operation[];
  outputFormat: string;
  quality: number;
  addOperation: (op: Operation) => void;
  removeOperation: (index: number) => void;
  updateOperation: (index: number, op: Operation) => void;
  clearOperations: () => void;
  setOutputFormat: (format: string) => void;
  setQuality: (quality: number) => void;
  
  // Jobs
  jobs: Job[];
  setJobs: (jobs: Job[]) => void;
  updateJob: (jobId: string, updates: Partial<Job>) => void;
  
  // UI
  sidebarOpen: boolean;
  activeCategory: string;
  setSidebarOpen: (open: boolean) => void;
  setActiveCategory: (category: string) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // User
      user: null,
      token: null,
      setUser: (user) => set({ user }),
      setToken: (token) => {
        set({ token });
        if (typeof window !== 'undefined') {
          if (token) {
            localStorage.setItem('token', token);
          } else {
            localStorage.removeItem('token');
          }
        }
      },
      logout: () => {
        set({ user: null, token: null, projects: [], activeProjectId: null });
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
        }
      },
      
      // Images
      images: [],
      selectedImageIds: [],
      setImages: (images) => set((state) => {
        // Clean up selectedImageIds - remove IDs that no longer exist
        const existingIds = new Set(images.map(img => img.id));
        const validSelectedIds = state.selectedImageIds.filter(id => existingIds.has(id));
        return { images, selectedImageIds: validSelectedIds };
      }),
      addImages: (newImages) => set((state) => ({ 
        images: [...state.images, ...newImages] 
      })),
      removeImage: (id) => set((state) => ({
        images: state.images.filter((img) => img.id !== id),
        selectedImageIds: state.selectedImageIds.filter((imgId) => imgId !== id),
      })),
      removeImages: (ids) => set((state) => {
        const idsSet = new Set(ids);
        return {
          images: state.images.filter((img) => !idsSet.has(img.id)),
          selectedImageIds: state.selectedImageIds.filter((imgId) => !idsSet.has(imgId)),
        };
      }),
      toggleImageSelection: (id) => set((state) => {
        // Only allow selecting images that exist
        const imageExists = state.images.some(img => img.id === id);
        if (!imageExists) return state;
        
        return {
          selectedImageIds: state.selectedImageIds.includes(id)
            ? state.selectedImageIds.filter((imgId) => imgId !== id)
            : [...state.selectedImageIds, id],
        };
      }),
      selectAllImages: () => set((state) => ({
        selectedImageIds: state.images.map((img) => img.id),
      })),
      selectImages: (ids) => set((state) => {
        // Only select IDs that exist in images
        const existingIds = new Set(state.images.map(img => img.id));
        const validIds = ids.filter(id => existingIds.has(id));
        return { selectedImageIds: validIds };
      }),
      clearSelection: () => set({ selectedImageIds: [] }),
      
      // Projects
      projects: [],
      activeProjectId: null,
      setProjects: (projects) => set({ projects }),
      addProject: (project) => set((state) => ({ 
        projects: [project, ...state.projects] 
      })),
      updateProject: (id, updates) => set((state) => ({
        projects: state.projects.map(p => p.id === id ? { ...p, ...updates } : p),
      })),
      removeProject: (id) => set((state) => ({
        projects: state.projects.filter(p => p.id !== id),
        activeProjectId: state.activeProjectId === id ? null : state.activeProjectId,
      })),
      setActiveProjectId: (projectId) => set({ activeProjectId: projectId, selectedImageIds: [] }),
      
      // Operations
      operations: [],
      outputFormat: 'webp',
      quality: 85,
      addOperation: (op) => set((state) => ({ 
        operations: [...state.operations, op] 
      })),
      removeOperation: (index) => set((state) => ({
        operations: state.operations.filter((_, i) => i !== index),
      })),
      updateOperation: (index, op) => set((state) => ({
        operations: state.operations.map((o, i) => (i === index ? op : o)),
      })),
      clearOperations: () => set({ operations: [] }),
      setOutputFormat: (format) => set({ outputFormat: format }),
      setQuality: (quality) => set({ quality }),
      
      // Jobs
      jobs: [],
      setJobs: (jobs) => set({ jobs }),
      updateJob: (jobId, updates) => set((state) => ({
        jobs: state.jobs.map((job) =>
          job.jobId === jobId ? { ...job, ...updates } : job
        ),
      })),
      
      // UI
      sidebarOpen: true,
      activeCategory: 'resize',
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setActiveCategory: (category) => set({ activeCategory: category }),
    }),
    {
      name: 'imagemagick-webgui-storage',
      partialize: (state) => ({
        token: state.token,
        outputFormat: state.outputFormat,
        quality: state.quality,
      }),
    }
  )
);
