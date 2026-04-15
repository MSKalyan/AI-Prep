import { apiClient } from '@/lib/apiClient';

export interface ApiError {
  message: string;
  status?: number;
  errors?: Record<string, string[]>;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  password_confirm: string;
  full_name?: string;
}

export interface Profile {
  id: number;
  email: string;
  username: string;
  full_name: string;
}

export interface UpdateProfilePayload {
  full_name?: string;
  username?: string;
  password?: string;
}

export const login = async (payload: LoginPayload) => {
  try {
    const { data } = await apiClient.post('/auth/login/', payload);
    return data;
  } catch (error: unknown) {
    const err = error as { response?: { data?: { message?: string } } };
    const apiError: ApiError = {
      message: err?.response?.data?.message || 'Invalid email or password',
      status:
        error instanceof Error
          ? undefined
          : (error as { response?: { status?: number } }).response?.status,
      errors: undefined,
    };
    throw apiError;
  }
};

export const register = async (payload: RegisterPayload) => {
  try {
    const { data } = await apiClient.post('/auth/register/', payload);
    return data;
  } catch (error: unknown) {
    const err = error as {
      response?: { data?: { message?: string; detail?: string; [key: string]: unknown } };
    };
    const response = err?.response?.data;

    const apiError: ApiError = {
      message: response?.message || response?.detail || 'Registration failed',
      status:
        error instanceof Error
          ? undefined
          : (error as { response?: { status?: number } }).response?.status,
      errors: response as Record<string, string[]> | undefined,
    };

    throw apiError;
  }
};

export const getProfile = async (): Promise<Profile | null> => {
  try {
    const { data } = await apiClient.get('/auth/profile/');
    return data;
  } catch (error: unknown) {
    const err = error as { response?: { status?: number } };
    if (err.response?.status === 401) {
      return null;
    }
    throw error;
  }
};

export const updateProfile = async (payload: UpdateProfilePayload) => {
  const { data } = await apiClient.patch('/auth/profile/', payload);
  return data;
};

export const logout = async () => {
  await apiClient.post('/auth/logout/');
};
