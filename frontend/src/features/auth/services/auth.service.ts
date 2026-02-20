import { apiClient } from "@/lib/apiClient";

export const login = async (payload: any) => {
  const { data } = await apiClient.post("/auth/login/", payload);
  return data;
};

export const register = async (payload: any) => {
  const { data } = await apiClient.post("/auth/register/", payload);
  return data;
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
  await apiClient.post("/auth/logout/");
};
