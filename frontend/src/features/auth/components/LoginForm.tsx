"use client";

import { useState } from "react";
import { useAuth } from "../hooks/useAuth";

export default function LoginForm() {

  const { login } = useAuth();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  return (

    <div className="flex min-h-screen items-center justify-center bg-gray-100">

      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-md">

        <h2 className="mb-6 text-center text-2xl font-semibold">
          Login
        </h2>

        <div className="space-y-4">

          <input
            className="w-full rounded-md border border-gray-300 p-2 focus:border-blue-500 focus:outline-none"
            placeholder="Email"
            type="email"
            value={form.email}
            onChange={(e) =>
              setForm({ ...form, email: e.target.value })
            }
          />

          <input
            className="w-full rounded-md border border-gray-300 p-2 focus:border-blue-500 focus:outline-none"
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) =>
              setForm({ ...form, password: e.target.value })
            }
          />

          <button
            className="w-full rounded-md bg-blue-600 p-2 text-white transition hover:bg-blue-700"
            onClick={() => login(form)}
          >
            Login
          </button>

        </div>

      </div>

    </div>
  );
}
