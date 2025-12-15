import axios from 'axios';

// Dynamic API URL - automatically detects if behind reverse proxy
const getApiUrl = (): string => {
  // In browser
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // If using standard ports (80/443) or reverse proxy → no port needed
    // API will be at same host as frontend (reverse proxy handles routing)
    if (!port || port === '80' || port === '443') {
      return `${protocol}//${hostname}`;
    }
    
    // If custom port (like localhost:3012) → use API port
    const apiPort = process.env.NEXT_PUBLIC_API_PORT || '8000';
    return `${protocol}//${hostname}:${apiPort}`;
  }
  
  // Server-side rendering - use env or localhost
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

// Create axios instance
export const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes
});

// Set baseURL dynamically before each request
api.interceptors.request.use((config) => {
  // Set dynamic baseURL
  config.baseURL = getApiUrl();
  
  // Add auth token
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auth API
export const authApi = {
  register: async (email: string, password: string, name?: string) => {
    const { data } = await api.post('/api/auth/register', { email, password, name });
    return data;
  },
  
  login: async (email: string, password: string) => {
    const { data } = await api.post('/api/auth/login', { email, password });
    return data;
  },
  
  me: async () => {
    const { data } = await api.get('/api/auth/me');
    return data;
  },
  
  logout: () => {
    localStorage.removeItem('token');
  },
  
  googleStatus: async () => {
    const { data } = await api.get('/api/auth/google/status');
    return data;
  },
  
  googleAuthUrl: async () => {
    const { data } = await api.get('/api/auth/google/auth-url');
    return data;
  },
  
  googleCallback: async (code: string, redirectUri: string) => {
    const { data } = await api.post('/api/auth/google/callback', { code, redirect_uri: redirectUri });
    return data;
  },
};

// Images API
export const imagesApi = {
  upload: async (files: File[], projectId?: number, onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    if (projectId) {
      formData.append('project_id', projectId.toString());
    }
    
    const { data } = await api.post('/api/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
        }
      },
    });
    return data;
  },
  
  list: async (skip = 0, limit = 50, projectId?: number | null) => {
    let url = `/api/images/?skip=${skip}&limit=${limit}`;
    if (projectId) {
      url += `&project_id=${projectId}`;
    }
    const { data } = await api.get(url);
    return data;
  },
  
  // Dynamic URL for image src
  get: (imageId: number) => {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      const port = window.location.port;
      
      // If standard ports or reverse proxy → no port
      if (!port || port === '80' || port === '443') {
        return `${protocol}//${hostname}/api/images/${imageId}`;
      }
      
      // If custom port → use API port
      const apiPort = process.env.NEXT_PUBLIC_API_PORT || '8000';
      return `${protocol}//${hostname}:${apiPort}/api/images/${imageId}`;
    }
    return `http://localhost:8000/api/images/${imageId}`;
  },
  
  // Dynamic URL for thumbnail src
  getThumbnail: (imageId: number) => {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      const port = window.location.port;
      
      // If standard ports or reverse proxy → no port
      if (!port || port === '80' || port === '443') {
        return `${protocol}//${hostname}/api/images/${imageId}/thumbnail`;
      }
      
      // If custom port → use API port
      const apiPort = process.env.NEXT_PUBLIC_API_PORT || '8000';
      return `${protocol}//${hostname}:${apiPort}/api/images/${imageId}/thumbnail`;
    }
    return `http://localhost:8000/api/images/${imageId}/thumbnail`;
  },
  
  getInfo: async (imageId: number) => {
    const { data } = await api.get(`/api/images/${imageId}/info`);
    return data;
  },
  
  getDetails: async (imageId: number) => {
    const { data } = await api.get(`/api/images/${imageId}`);
    return data;
  },
  
  delete: async (imageId: number) => {
    await api.delete(`/api/images/${imageId}`);
  },
  
  bulkDelete: async (imageIds: number[]) => {
    await api.post('/api/images/bulk-delete', { image_ids: imageIds });
  },
  
  downloadZip: async (imageIds: number[]) => {
    const { data } = await api.post('/api/images/download-zip', { image_ids: imageIds }, {
      responseType: 'blob',
    });
    return data;
  },
  
  moveToProject: async (imageIds: number[], projectId: number | null) => {
    const { data } = await api.post('/api/images/move-to-project', {
      image_ids: imageIds,
      project_id: projectId
    });
    return data;
  },
};

// Operations API
export const operationsApi = {
  process: async (imageIds: number[], operations: any[], outputFormat = 'webp', quality = 85) => {
    const { data } = await api.post('/api/operations/process', {
      image_ids: imageIds,
      operations,
      output_format: outputFormat,
      quality,
    });
    return data;
  },
  
  processSync: async (imageId: number, operations: any[], outputFormat = 'webp', quality = 85) => {
    const { data } = await api.post('/api/operations/process-sync', {
      image_id: imageId,
      operations,
      output_format: outputFormat,
      quality,
    });
    return data;
  },
  
  processRaw: async (imageIds: number[], command: string, outputFormat = 'png') => {
    const { data } = await api.post('/api/operations/raw', {
      image_ids: imageIds,
      command,
      output_format: outputFormat,
    });
    return data;
  },
  
  previewCommand: async (operations: any[], outputFormat = 'webp', quality = 85) => {
    const { data } = await api.post('/api/operations/preview-command', {
      operations,
      output_format: outputFormat,
      quality,
    });
    return data;
  },
  
  getAvailable: async () => {
    const { data } = await api.get('/api/operations/available');
    return data;
  },
  
  preview: async (imageId: number, operations: any[]) => {
    const { data } = await api.post('/api/operations/preview', {
      image_id: imageId,
      operations,
    });
    return data;
  },
  
  removeBackground: async (imageId: number) => {
    const { data } = await api.post('/api/operations/remove-background', {
      image_id: imageId,
    });
    return data;
  },
  
  aiStatus: async () => {
    const { data } = await api.get('/api/operations/ai-status');
    return data;
  },
};

// Queue API
export const queueApi = {
  getStats: async () => {
    const { data } = await api.get('/api/queue/stats');
    return data;
  },
  
  listJobs: async (status?: string, limit = 50) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    const { data } = await api.get(`/api/queue/jobs?${params}`);
    return data;
  },
  
  getJob: async (jobId: string) => {
    const { data } = await api.get(`/api/queue/jobs/${jobId}`);
    return data;
  },
  
  cancelJob: async (jobId: string) => {
    await api.post(`/api/queue/jobs/${jobId}/cancel`);
  },
  
  downloadResults: async (jobId: string) => {
    const { data } = await api.get(`/api/queue/jobs/${jobId}/download`, {
      responseType: 'blob',
    });
    return data;
  },
  
  deleteJob: async (jobId: string) => {
    await api.delete(`/api/queue/jobs/${jobId}`);
  },
};

// Settings API
export const settingsApi = {
  get: async () => {
    const { data } = await api.get('/api/settings/');
    return data;
  },
  
  update: async (settings: any) => {
    const { data } = await api.put('/api/settings/', settings);
    return data;
  },
  
  reset: async () => {
    await api.post('/api/settings/reset');
  },
};

// Projects API
export const projectsApi = {
  list: async () => {
    const { data } = await api.get('/api/projects/');
    return data;
  },
  
  create: async (name: string, description?: string, color?: string) => {
    const { data } = await api.post('/api/projects/', { name, description, color });
    return data;
  },
  
  get: async (projectId: number) => {
    const { data } = await api.get(`/api/projects/${projectId}`);
    return data;
  },
  
  update: async (projectId: number, updates: { name?: string; description?: string; color?: string }) => {
    const { data } = await api.put(`/api/projects/${projectId}`, updates);
    return data;
  },
  
  delete: async (projectId: number) => {
    await api.delete(`/api/projects/${projectId}`);
  },
  
  // Add images to project
  addImages: async (projectId: number, imageIds: number[]) => {
    const { data } = await api.post('/api/images/move-to-project', {
      image_ids: imageIds,
      project_id: projectId
    });
    return data;
  },
  
  // Remove images from project (set project_id to null)
  removeImages: async (imageIds: number[]) => {
    const { data } = await api.post('/api/images/move-to-project', {
      image_ids: imageIds,
      project_id: null
    });
    return data;
  },
};

// History API
export const historyApi = {
  list: async (skip = 0, limit = 50) => {
    const { data } = await api.get(`/api/history/?skip=${skip}&limit=${limit}`);
    return data;
  },
  
  get: async (historyId: number) => {
    const { data } = await api.get(`/api/history/${historyId}`);
    return data;
  },
  
  delete: async (historyId: number) => {
    await api.delete(`/api/history/${historyId}`);
  },
  
  getStats: async () => {
    const { data } = await api.get('/api/history/stats');
    return data;
  },
};

// Export getApiUrl for use elsewhere if needed
export { getApiUrl };
