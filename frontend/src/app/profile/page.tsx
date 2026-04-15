'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/features/auth';
import { useRouter } from 'next/navigation';

export default function ProfilePage() {
  const { user, isLoading, updateProfile } = useAuth();
  const router = useRouter();

  const [form, setForm] = useState({
    full_name: null as string | null,
    username: null as string | null,
    password: '',
  });

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace('/login');
    }
  }, [isLoading, user, router]);

  const submit = async () => {
    if (!user) return;

    const payload: { full_name?: string; username?: string; password?: string } = {};

    const fullName = (form.full_name ?? user.full_name ?? '').trim();
    const username = (form.username ?? user.username ?? '').trim();
    const password = form.password.trim();

    if (fullName !== (user.full_name || '')) payload.full_name = fullName;
    if (username !== (user.username || '')) payload.username = username;
    if (password) payload.password = password;

    if (Object.keys(payload).length === 0) return;

    await updateProfile(payload);
  };

  if (isLoading) return <p className="p-10 text-center text-gray-500">Loading...</p>;

  if (!user) return null;

  return (
    <div className="min-h-screen bg-white text-black">
      <div className="max-w-md mx-auto px-4 sm:px-6 py-8 sm:py-10">
        {/* HEADER */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">Profile Settings</h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">Update your account information</p>
        </div>

        {/* CARD */}
        <div className="border border-gray-200 rounded-2xl p-4 sm:p-6 space-y-6">
          {/* FORM */}
          <div className="space-y-5">
            {/* Full Name */}
            <div className="space-y-1">
              <label htmlFor="full_name" className="text-xs sm:text-sm text-gray-600">Full Name</label>
              <input
                id="full_name"
                placeholder="Your full name"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
                value={form.full_name ?? user.full_name ?? ''}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </div>

            {/* Username */}
            <div className="space-y-1">
              <label htmlFor="username" className="text-xs sm:text-sm text-gray-600">Username</label>
              <input
                id="username"
                placeholder="Your username"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
                value={form.username ?? user.username ?? ''}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
              />
            </div>

            {/* Password */}
            <div className="space-y-1">
              <label htmlFor="password" className="text-xs sm:text-sm text-gray-600">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Leave blank to keep current password"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
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
