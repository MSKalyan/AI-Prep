import axios from "axios";

export const apiClient = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    // Do not intercept refresh endpoint
    if (originalRequest?.url?.includes("/auth/refresh/")) {
      return Promise.reject(error);
    }

    // Handle expired access token
    if (error.response?.status === 401 && !originalRequest?._retry) {

      // If already on login page, do nothing
      if (typeof window !== "undefined" && window.location.pathname === "/login") {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      try {
        await apiClient.post("/auth/refresh/");
        return apiClient(originalRequest);
      } catch (refreshError) {
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    // IMPORTANT: forward all other errors (e.g., 400 validation errors)
    return Promise.reject(error);
  }
);