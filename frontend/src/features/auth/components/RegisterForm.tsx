"use client";

import { useState } from "react";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { ApiError } from "@/features/auth/types/apiError";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

export default function RegisterForm() {
  const { register, registerLoading } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    password_confirm: "",
    full_name: "",
  });

  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (form.password !== form.password_confirm) {
      setError("Passwords do not match");
      return;
    }

    try {
      await register(form);

      await queryClient.refetchQueries({
        queryKey: ["profile"],
      });

      router.replace("/dashboard");
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white text-black px-4 sm:px-6 py-8 sm:py-12">

      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md border border-gray-200 rounded-2xl p-4 sm:p-6 space-y-4 sm:space-y-5"
      >

        {/* HEADER */}
        <div className="text-center mb-3 sm:mb-4">
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">
            Create Account
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            Start your exam preparation journey
          </p>
        </div>

        {/* ERROR */}
        {error && (
          <div className="text-xs sm:text-sm border border-gray-300 bg-gray-50 rounded-lg p-3">
            {error}
          </div>
        )}

        {/* INPUTS */}
        <div className="space-y-3 sm:space-y-4">

          <div className="space-y-1">
            <label htmlFor="full_name" className="text-xs sm:text-sm text-gray-600">Full Name</label>
            <input
              id="full_name"
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="username" className="text-xs sm:text-sm text-gray-600">Username</label>
            <input
              id="username"
              name="username"
              value={form.username}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="email" className="text-xs sm:text-sm text-gray-600">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="password" className="text-xs sm:text-sm text-gray-600">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="password_confirm" className="text-xs sm:text-sm text-gray-600">Confirm Password</label>
            <input
              id="password_confirm"
              name="password_confirm"
              type="password"
              value={form.password_confirm}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
            />
          </div>

        </div>

        {/* BUTTON */}
        <button
          type="submit"
          disabled={registerLoading}
          className="w-full rounded-lg bg-black text-white py-2 text-sm sm:text-base font-medium hover:opacity-80 transition disabled:opacity-50"
        >
          {registerLoading ? "Registering..." : "Register"}
        </button>

        {/* LOGIN LINK */}
        <p className="text-xs sm:text-sm text-center text-gray-600">
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-black font-medium hover:underline"
          >
            Login
          </Link>
        </p>

      </form>

    </div>
  );
}