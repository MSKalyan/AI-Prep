import { apiClient } from "@/lib/apiClient";
import {ApiError} from "@/features/auth/types/apiError";


export const login = async (payload: any) => {
  try {

    const { data } = await apiClient.post("/auth/login/", payload);

    return data;

  } catch (error: any) {

    const apiError: ApiError = {
      message:
        error?.response?.data?.message ||
        "Invalid email or password",
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
  } catch (error: any) {
    const response = error?.response?.data;
console.log("REGISTER ERROR RESPONSE:", error?.response?.data);
    let message = "Registration failed";

    if (response) {
      if (response.message) {
        message = response.message;
      } else if (response.detail) {
        message = response.detail;
      } else if (typeof response === "object") {
        const messages = Object.values(response)
          .flat()
          .filter(Boolean)
          .join(" ");

        if (messages) {
          message = messages;
        }
      }
    }

    const apiError: ApiError = {
      message,
      status: error?.response?.status,
      errors: response,
    };

    throw apiError;
  }
};

export const getProfile = async () => {
  try {
    const { data } = await apiClient.get("/auth/profile/");
    return data;
  } catch (error: any) {

    // 401 means NOT logged in — not an error
    if (error.response?.status === 401) {
      return null;
    }

    throw error;
  }
};

export async function updateProfile(payload:any){
  const { data } = await apiClient.patch("/auth/profile/", payload);
  return data;
}


export const logout = async () => {
  console.log("logout called");
  await apiClient.post("/auth/logout/");
};
