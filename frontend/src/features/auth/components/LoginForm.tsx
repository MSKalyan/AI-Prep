"use client";

import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

export default function LoginForm() {

  const { login, loginError, loginLoading } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");

  const handleLogin = async () => {

    setError("");

    if (!form.email) {
      setError("Email is required");
      return;
    }

    if (!form.password) {
      setError("Password is required");
      return;
    }

    try {
      await login(form);
      // Refetch profile to ensure authentication state is updated
      await queryClient.refetchQueries({
        queryKey: ["profile"],
      });
      // If login succeeds, redirect manually
      router.replace("/dashboard");
    } catch {
      // error handled by React Query
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">

      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-md">

        <h2 className="mb-6 text-center text-2xl font-semibold">
          Login
        </h2>

        <div className="space-y-4">

          {/* Client Validation Error */}
          {error && (
            <div className="rounded bg-red-100 p-2 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Server Error */}
          {loginError && (
            <div className="rounded bg-red-100 p-2 text-sm text-red-700">
              {loginError.message}
            </div>
          )}

          <input
            type="email"
            placeholder="Email"
            className="w-full rounded border p-2"
            value={form.email}
            onChange={(e) =>
              setForm({ ...form, email: e.target.value })
            }
          />

          <input
            type="password"
            placeholder="Password"
            className="w-full rounded border p-2"
            value={form.password}
            onChange={(e) =>
              setForm({ ...form, password: e.target.value })
            }
          />

          <button
            type="button"
            onClick={handleLogin}
            disabled={loginLoading}
            className="w-full rounded bg-blue-600 p-2 text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loginLoading ? "Logging in..." : "Login"}
          </button>

        </div>

      </div>

    </div>
  );
}