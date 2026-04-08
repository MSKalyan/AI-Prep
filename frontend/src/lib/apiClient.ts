import axios from "axios";


const API=process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const apiClient = axios.create({
  baseURL: `${API}/api`,
  withCredentials: true,
});
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    if (originalRequest?.url?.includes("/auth/refresh/")) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest?._retry) {

      if (typeof window !== "undefined" && window.location.pathname === "/login") {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      try {
        await apiClient.post("/auth/refresh/");
        return apiClient(originalRequest);
      } catch (refreshError) {
        return Promise.reject(refreshError);
        }
    }

    return Promise.reject(error);
  }
);