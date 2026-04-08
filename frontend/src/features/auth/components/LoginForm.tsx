"use client";

import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

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

      await queryClient.refetchQueries({
        queryKey: ["profile"],
      });

      router.replace("/dashboard");
    } catch {}
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white text-black px-4 sm:px-6 py-8 sm:py-12">

      <div className="w-full max-w-md">

        {/* HEADER */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold tracking-tight">
            Login
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Access your account
          </p>
        </div>

        {/* CARD */}
        <div className="border border-gray-200 rounded-2xl p-6 space-y-5">

          {/* Errors */}
          {(error || loginError) && (
            <div className="text-sm text-black border border-gray-300 bg-gray-50 rounded-lg p-3">
              {error || loginError?.message}
            </div>
          )}

          {/* Email */}
          <div className="space-y-1">
            <label htmlFor="email" className="text-sm text-gray-600">Email</label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
              value={form.email}
              onChange={(e) =>
                setForm({ ...form, email: e.target.value })
              }
            />
          </div>

          {/* Password */}
          <div className="space-y-1">
            <label htmlFor="password" className="text-sm text-gray-600">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
              value={form.password}
              onChange={(e) =>
                setForm({ ...form, password: e.target.value })
              }
            />
          </div>

          {/* Button */}
          <button
            type="button"
            onClick={handleLogin}
            disabled={loginLoading}
            className="w-full rounded-lg bg-black text-white py-2 text-sm font-medium hover:opacity-80 transition disabled:opacity-50"
          >
            {loginLoading ? "Logging in..." : "Login"}
          </button>

          {/* CREATE ACCOUNT LINK */}
          <p className="text-sm text-center text-gray-600">
            Don’t have an account?{" "}
            <Link
              href="/register"
              className="text-black font-medium hover:underline"
            >
              Create account
            </Link>
          </p>

        </div>

      </div>

    </div>
  );
}