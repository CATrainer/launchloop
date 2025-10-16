import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login if unauthorized
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  signup: (data: { email: string; password: string }) =>
    api.post('/auth/signup', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
};

// Projects endpoints
export const projectsAPI = {
  list: () => api.get('/projects'),
  get: (id: string) => api.get(`/projects/${id}`),
  create: (data: { name: string }) => api.post('/projects', data),
  update: (id: string, data: any) => api.patch(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  publish: (id: string) => api.post(`/projects/${id}/publish`),
  unpublish: (id: string) => api.post(`/projects/${id}/unpublish`),
  saveState: (id: string, state: any) => api.post(`/projects/${id}/save-state`, state),
};

// Generation endpoints
export const generateAPI = {
  extract: (description: string) =>
    api.post('/generate/extract', { description }),
  questions: (data: { template_id: string; extracted_data: any }) =>
    api.post('/generate/questions', data),
  create: (data: any) => api.post('/generate', data),
  get: (id: string) => api.get(`/generate/${id}`),
  retry: (id: string) => api.post(`/generate/${id}/retry`),
  templates: () => api.get('/generate/templates'),
};

// Signups endpoints
export const signupsAPI = {
  list: (projectId: string) => api.get(`/signups/project/${projectId}`),
  export: (projectId: string) => api.get(`/signups/project/${projectId}/export`),
};
