import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // In a real app, get token from local storage or state
    // const token = localStorage.getItem('token');
    // if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

export const eventService = {
  getEvents: async (params?: any) => {
    const response = await api.get('/events', { params });
    return response.data;
  },
  getEvent: async (id: string) => {
    const response = await api.get(`/events/${id}`);
    return response.data;
  },
  getDashboardStats: async () => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },
  getHeatmapData: async () => {
    const response = await api.get('/events/heatmap/data');
    return response.data;
  }
};

export const predictionService = {
  predictImpact: async (data: any) => {
    const response = await api.post('/predictions/predict', data);
    return response.data;
  },
  getModelInfo: async () => {
    const response = await api.get('/predictions/model-info');
    return response.data;
  }
};

export const analyticsService = {
  getOverview: async () => {
    const response = await api.get('/analytics/overview');
    return response.data;
  },
  getLeaderboard: async () => {
    const response = await api.get('/leaderboard');
    return response.data;
  }
};

export default api;
