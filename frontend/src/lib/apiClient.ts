import axios from "axios";

export const apiClient = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true,
});




apiClient.interceptors.response.use(
  res => res,
  async error => {

    const originalRequest = error.config;

    // ❌ DO NOT intercept refresh endpoint itself
    if (originalRequest.url?.includes("/auth/refresh/")) {
      return Promise.reject(error);
    }

   if (error.response?.status === 401 && !originalRequest._retry) {

  // 🚨 skip refresh if already logout state
  if (window.location.pathname === "/login") {
      return Promise.reject(error);
  }

  originalRequest._retry = true;

  try {
    await apiClient.post("/auth/refresh/");
    return apiClient(originalRequest);
  } catch {
    window.location.href = "/login";
    return Promise.reject(error);
  }
}
  }
);
