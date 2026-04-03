"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as auth from "../services/auth.service";
import { useRouter } from "next/navigation";
import { ApiError } from "../types/apiError";
import { register } from "module";
export function useAuth(){

  const queryClient = useQueryClient();
  const router = useRouter();


const profileQuery = useQuery({
  queryKey: ["profile"],
  queryFn: auth.getProfile,
  retry: false,
  staleTime: 5 * 60 * 1000,   // ✅ NOT Infinity, NOT 0
  refetchOnMount: false,      // 🔥 IMPORTANT
  refetchOnWindowFocus: false,
});


  const loginMutation = useMutation<
  any,
  ApiError,
  { email: string; password: string }
>({
  mutationFn: auth.login,

  onSuccess: async () => {

 await queryClient.invalidateQueries({
    queryKey: ["profile"],
  });
    router.replace("/dashboard");
  },

  onError: (error) => {

    console.error("Login failed:", error.message);

  }
});


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

  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: ["profile"] });
    router.push("/dashboard");
  },

  onError: (error) => {
    console.error("Registration failed:", error.message);
  }
});

 const logoutMutation = useMutation({
  mutationFn: auth.logout,
  onSuccess: () => {
     queryClient.clear();

     router.replace("/login");
  }
});


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
