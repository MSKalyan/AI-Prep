import { apiClient } from "@/lib/apiClient";

export interface ApiError {
  message: string;
  status?: number;
  errors?: Record<string, string[]>;
}

export const login = async (payload: any) => {
  try {
    const { data } = await apiClient.post("/auth/login/", payload);
    return data;
  } catch (error: any) {
    const apiError: ApiError = {
      message: error?.response?.data?.message || "Invalid email or password",
      status: error?.response?.status,
      errors: error?.response?.data?.errors,
    };
    throw apiError;
  }
};

export const register = async (payload: any) => {
  try {
    const { data } = await apiClient.post("/auth/register/", payload);
    return data;
  }catch (error: any) {
  const response = error?.response?.data;

  const apiError: ApiError = {
    message:
      response?.message ||
      response?.detail ||
      "Registration failed",
    status: error?.response?.status,
    errors: response, // keep structured errors intact
  };

  throw apiError;
}
};

export const getProfile = async () => {
  try {
    const { data } = await apiClient.get("/auth/profile/");
    return data;
  } catch (error: any) {
    if (error.response?.status === 401) {
      return null;
    }
    throw error;
  }
};

export const updateProfile = async (payload: any) => {
  const { data } = await apiClient.patch("/auth/profile/", payload);
  return data;
};

export const logout = async () => {
  await apiClient.post("/auth/logout/");
};

