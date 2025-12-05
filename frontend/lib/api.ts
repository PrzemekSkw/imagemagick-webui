import axios from 'axios';

// Detect API URL - use NEXT_PUBLIC_API_URL or default to current host with port 8000
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    // In browser - check env var first, then fall back to same host on port 8000
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl) return envUrl;
    
    // Use same hostname but port 8000
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  // Server-side - use localhost
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_URL = getApiUrl();

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second default timeout
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Add response error interceptor for better debugging
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('Network error - backend may be unreachable at:', API_URL);
    }
    return Promise.reject(error);
  }
);

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
  
  registrationStatus: async () => {
    const { data } = await api.get('/api/auth/registration-status');
    return data;
  },
  
  changePassword: async (currentPassword: string, newPassword: string) => {
    const { data } = await api.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return data;
  },
  
  createUser: async (email: string, password: string, isAdmin: boolean = false) => {
    const { data } = await api.post('/api/auth/create-user', {
      email,
      password,
      is_admin: isAdmin,
    });
    return data;
  },
  
  // Google OAuth
  googleStatus: async () => {
    // Add timestamp to prevent caching
    const { data } = await api.get(`/api/auth/google/status?_t=${Date.now()}`);
    return data;
  },
  
  googleAuthUrl: async () => {
    const { data } = await api.get('/api/auth/google');
    return data;
  },
  
  googleCallback: async (code: string, redirectUri: string) => {
    const { data } = await api.post('/api/auth/google/callback', {
      code,
      redirect_uri: redirectUri,
    });
    return data;
  },
};

// Images API
export const imagesApi = {
  upload: async (files: File[], onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    
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
  
  list: async (skip = 0, limit = 50) => {
    const { data } = await api.get(`/api/images?skip=${skip}&limit=${limit}`);
    return data;
  },
  
  get: (imageId: number) => `${API_URL}/api/images/${imageId}`,
  
  getThumbnail: (imageId: number) => `${API_URL}/api/images/${imageId}/thumbnail`,
  
  getInfo: async (imageId: number) => {
    const { data } = await api.get(`/api/images/${imageId}/info`);
    return data;
  },
  
  delete: async (imageId: number) => {
    await api.delete(`/api/images/${imageId}`);
  },
  
  downloadZip: async (imageIds: number[]) => {
    const { data } = await api.post('/api/images/download-zip', imageIds, {
      responseType: 'blob',
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
  
  // Synchronous processing for single image - instant results
  processSync: async (imageId: number, operations: any[], outputFormat = 'webp') => {
    const { data } = await api.post('/api/operations/process-sync', {
      image_id: imageId,
      operations,
      output_format: outputFormat,
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
  
  // AI: Upscale image (longer timeout - can take time)
  upscale: async (imageId: number, scale: number = 2, method: string = 'lanczos') => {
    const { data } = await api.post('/api/operations/upscale', {
      image_id: imageId,
      scale,
      method,
    }, { timeout: 120000 }); // 2 minute timeout
    return data;
  },
  
  // AI: Remove background (longer timeout - can take 60+ seconds)
  removeBackground: async (imageId: number, alphaMatting: boolean = true) => {
    const { data } = await api.post('/api/operations/remove-background-sync', {
      image_id: imageId,
      alpha_matting: alphaMatting,
    }, { timeout: 180000 }); // 3 minute timeout
    return data;
  },
  
  // Get AI capabilities
  getAiCapabilities: async () => {
    const { data } = await api.get('/api/operations/ai-capabilities');
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
  
  // Alias for downloadResults
  downloadJob: async (jobId: string) => {
    const { data } = await api.get(`/api/queue/jobs/${jobId}/download`, {
      responseType: 'blob',
    });
    return data;
  },
  
  // Download single file from job
  downloadJobFile: async (jobId: string, fileIndex: number) => {
    const { data } = await api.get(`/api/queue/jobs/${jobId}/files/${fileIndex}`, {
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
    const { data } = await api.get('/api/settings');
    return data;
  },
  
  update: async (settings: any) => {
    const { data } = await api.put('/api/settings', settings);
    return data;
  },
  
  reset: async () => {
    await api.post('/api/settings/reset');
  },
};

// Projects API
export const projectsApi = {
  list: async () => {
    const { data } = await api.get('/api/projects');
    return data;
  },
  
  create: async (name: string, description?: string, color?: string, icon?: string) => {
    const { data } = await api.post('/api/projects', { name, description, color, icon });
    return data;
  },
  
  get: async (projectId: number) => {
    const { data } = await api.get(`/api/projects/${projectId}`);
    return data;
  },
  
  update: async (projectId: number, updates: { name?: string; description?: string; color?: string; icon?: string }) => {
    const { data } = await api.put(`/api/projects/${projectId}`, updates);
    return data;
  },
  
  delete: async (projectId: number) => {
    const { data } = await api.delete(`/api/projects/${projectId}`);
    return data;
  },
  
  addImages: async (projectId: number, imageIds: number[]) => {
    const { data } = await api.post(`/api/projects/${projectId}/images`, { image_ids: imageIds });
    return data;
  },
  
  removeImages: async (imageIds: number[]) => {
    const { data } = await api.post('/api/projects/images/remove', { image_ids: imageIds });
    return data;
  },
  
  getImages: async (projectId: number) => {
    const { data } = await api.get(`/api/projects/${projectId}/images`);
    return data;
  },
};
