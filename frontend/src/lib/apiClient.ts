import axios from 'axios';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const apiClient = axios.create({
  baseURL: `${API}/api`,
  withCredentials: true,
});
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    const globalWindow = (globalThis as typeof globalThis & { window?: Window }).window;

    if (originalRequest?.url?.includes('/auth/refresh/')) {
      throw error;
    }

    if (error.response?.status === 401 && !originalRequest?._retry) {
      if (globalWindow?.location?.pathname === '/login') {
        throw error;
      }

      originalRequest._retry = true;

      try {
        await apiClient.post('/auth/refresh/');
        return apiClient(originalRequest);
      } catch (refreshError) {
        throw refreshError;
      }
    }

    throw error;
  }
);
