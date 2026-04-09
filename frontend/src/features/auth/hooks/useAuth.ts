"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { login, register, getProfile, updateProfile, logout, ApiError } from "../services/auth.service";
import { useRouter } from "next/navigation";

export function useAuth() {
  const queryClient = useQueryClient();
  const router = useRouter();

  const profileQuery = useQuery({
    queryKey: ["profile"],
    queryFn: getProfile,
    retry: false,
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  });

  const loginMutation = useMutation<any, ApiError, { email: string; password: string }>({
    mutationFn: login,
    onError: (error) => {
      console.error("Login failed:", error.message);
    },
  });

  const registerMutation = useMutation<any, ApiError, {
    email: string;
    username: string;
    password: string;
    password_confirm: string;
    full_name?: string;
  }>({
    mutationFn: register,
    onSuccess: async () => {
      await queryClient.refetchQueries({ queryKey: ["profile"] });
    },
    onError: (error) => {
      console.error("Registration failed:", error.message);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
      router.replace("/login");
    },
  });

  const updateProfileMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      router.push("/dashboard");
    },
  });

  return {
    user: profileQuery.data,
    isLoading: profileQuery.isLoading,
    isAuthenticated: !!profileQuery.data,
    login: loginMutation.mutateAsync,
    loginError: loginMutation.error,
    loginLoading: loginMutation.isPending,
    register: registerMutation.mutateAsync,
    registerError: registerMutation.error,
    registerLoading: registerMutation.isPending,
    logout: logoutMutation.mutateAsync,
    updateProfile: updateProfileMutation.mutateAsync,
  };
}
