"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as auth from "../services/auth.service";
import { useRouter } from "next/navigation";

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

  const loginMutation = useMutation({
    mutationFn: auth.login,
    onSuccess: () => {

      // force refetch user
      queryClient.invalidateQueries({ queryKey:["profile"] });

      router.push("/dashboard");
    }
  });

  // ===============================
  // REGISTER
  // ===============================

  const registerMutation = useMutation({
    mutationFn: auth.register,
    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey:["profile"] });

      router.push("/dashboard");
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
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    updateProfile: updateProfileMutation.mutateAsync,
  };
}
