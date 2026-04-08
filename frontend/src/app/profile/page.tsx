"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/features/auth/hooks/useAuth";

export default function ProfilePage() {
  const { user, isLoading, updateProfile } = useAuth();

  const [form, setForm] = useState({
    full_name: "",
    username: "",
    password: "",
  });

  useEffect(() => {
    if (user) {
      setForm({
        full_name: user.full_name || "",
        username: user.username || "",
        password: "",
      });
    }
  }, [user]);

  if (isLoading)
    return <p className="p-10 text-center text-gray-500">Loading...</p>;

  const submit = async () => {
    await updateProfile(form);
  };

  return (
    <div className="min-h-screen bg-white text-black">
      <div className="max-w-md mx-auto px-4 sm:px-6 py-8 sm:py-10">

        {/* HEADER */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">
            Profile Settings
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            Update your account information
          </p>
        </div>

        {/* CARD */}
        <div className="border border-gray-200 rounded-2xl p-4 sm:p-6 space-y-6">

          {/* FORM */}
          <div className="space-y-5">

            {/* Full Name */}
            <div className="space-y-1">
              <label className="text-xs sm:text-sm text-gray-600">
                Full Name
              </label>
              <input
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
                value={form.full_name}
                onChange={(e) =>
                  setForm({ ...form, full_name: e.target.value })
                }
              />
            </div>

            {/* Username */}
            <div className="space-y-1">
              <label className="text-xs sm:text-sm text-gray-600">
                Username
              </label>
              <input
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
                value={form.username}
                onChange={(e) =>
                  setForm({ ...form, username: e.target.value })
                }
              />
            </div>

            {/* Password */}
            <div className="space-y-1">
              <label className="text-xs sm:text-sm text-gray-600">
                Password
              </label>
              <input
                type="password"
                placeholder="Leave blank to keep current password"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
                value={form.password}
                onChange={(e) =>
                  setForm({ ...form, password: e.target.value })
                }
              />
              <p className="text-xs text-gray-500">
                Only fill this if you want to change your password
              </p>
            </div>

          </div>

          {/* ACTION */}
          <button
            className="w-full rounded-lg bg-black text-white py-2 text-sm font-medium hover:opacity-80 transition"
            onClick={submit}
          >
            Save Changes
          </button>

        </div>

      </div>
    </div>
  );
}