"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as auth from "../services/auth.service";
import { useRouter } from "next/navigation";
import { ApiError } from "../types/apiError";
import { register } from "module";
export function useAuth(){

  const queryClient = useQueryClient();
  const router = useRouter();

  // ===============================
  // GLOBAL USER QUERY
  // ===============================

  const profileQuery = useQuery({
    queryKey: ["profile"],
    queryFn: auth.getProfile,
    retry: false,
    staleTime: Infinity, // optional optimization
    // refetchInterval:10000, // auto refetch every 10s to keep user data fresh
  });

  // ===============================
  // LOGIN
  // ===============================

  const loginMutation = useMutation<
  any,
  ApiError,
  { email: string; password: string }
>({
  mutationFn: auth.login,

  onSuccess: () => {

    // refresh user profile
    queryClient.invalidateQueries({ queryKey: ["profile"] });

    router.push("/dashboard");
  },

  onError: (error) => {

    console.error("Login failed:", error.message);

  }
});

  // ===============================
  // REGISTER
  // ===============================

  const registerMutation = useMutation<
  any,
  ApiError,
  {
    email: string;
    username: string;
    password: string;
    password_confirm: string;
    full_name?: string;
  }
>({
  mutationFn: auth.register,

  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["profile"] });
    router.push("/dashboard");
  },

  onError: (error) => {
    console.error("Registration failed:", error.message);
  }
});

  // ===============================
  // LOGOUT
  // ===============================

 const logoutMutation = useMutation({
  mutationFn: auth.logout,
  onSuccess: () => {
    queryClient.setQueryData(["profile"], null);
    router.push("/login");
  }
});


  // ===============================
  // UPDATE PROFILE
  // ===============================

  const updateProfileMutation = useMutation({
    mutationFn: auth.updateProfile,
    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey:["profile"] });

      router.push("/dashboard");
    }
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
