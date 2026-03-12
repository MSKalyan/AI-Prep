"use client";

import { useState } from "react";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { ApiError } from "@/features/auth/types/apiError";

export default function RegisterForm() {

  const { register, registerLoading } = useAuth();

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

    } catch (err) {

      const apiError = err as ApiError;
      setError(apiError.message);

    }
  };

  return (

    <div className="flex min-h-screen items-center justify-center bg-gray-100">

      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-md"
      >

        <h2 className="mb-6 text-center text-2xl font-semibold">
          Create Account
        </h2>

        <div className="space-y-4">

          <input
            name="full_name"
            placeholder="Full name"
            value={form.full_name}
            onChange={handleChange}
            className="w-full rounded-md border border-gray-300 p-2"
          />

          <input
            name="username"
            placeholder="Username"
            value={form.username}
            onChange={handleChange}
            required
            className="w-full rounded-md border border-gray-300 p-2"
          />

          <input
            name="email"
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={handleChange}
            required
            className="w-full rounded-md border border-gray-300 p-2"
          />

          <input
            name="password"
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={handleChange}
            required
            className="w-full rounded-md border border-gray-300 p-2"
          />

          <input
            name="password_confirm"
            type="password"
            placeholder="Confirm Password"
            value={form.password_confirm}
            onChange={handleChange}
            required
            className="w-full rounded-md border border-gray-300 p-2"
          />

          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}

          <button
            type="submit"
            disabled={registerLoading}
            className="w-full rounded-md bg-blue-600 p-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {registerLoading ? "Registering..." : "Register"}
          </button>

        </div>

      </form>

    </div>
  );
}