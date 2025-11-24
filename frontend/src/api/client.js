import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// API methods
export const auth = {
  login: (credentials) => apiClient.post('/api/auth/login', credentials),
  register: (userData) => apiClient.post('/api/auth/register', userData),
};

export const users = {
  getMe: () => apiClient.get('/api/users/me'),
  list: (params) => apiClient.get('/api/users', { params }),
  get: (id) => apiClient.get(`/api/users/${id}`),
  update: (id, data) => apiClient.patch(`/api/users/${id}`, data),
  delete: (id) => apiClient.delete(`/api/users/${id}`),
};

export const tickets = {
  list: (params) => apiClient.get('/api/tickets', { params }),
  get: (id) => apiClient.get(`/api/tickets/${id}`),
  create: (data) => apiClient.post('/api/tickets', data),
  update: (id, data) => apiClient.patch(`/api/tickets/${id}`, data),
  delete: (id) => apiClient.delete(`/api/tickets/${id}`),
  assign: (id, assigneeId) => apiClient.post(`/api/tickets/${id}/assign`, null, {
    params: { assignee_id: assigneeId }
  }),
};

export const categories = {
  list: (params) => apiClient.get('/api/categories', { params }),
  get: (id) => apiClient.get(`/api/categories/${id}`),
  create: (data) => apiClient.post('/api/categories', data),
  delete: (id) => apiClient.delete(`/api/categories/${id}`),
};

export const comments = {
  list: (ticketId) => apiClient.get(`/api/comments/ticket/${ticketId}`),
  create: (data) => apiClient.post('/api/comments', data),
  delete: (id) => apiClient.delete(`/api/comments/${id}`),
};
