"use client";

import Link from "next/link";
import { useAuth } from "@/features/auth/hooks/useAuth";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-4">

        {/* LEFT SIDE */}
        <div className="flex items-center gap-8">

          {/* Logo */}
          <Link
            href="/"
            className="text-lg font-semibold tracking-tight hover:opacity-80 transition"
          >
            AI Exam Prep
          </Link>

          {/* Navigation Links */}
          {user && (
            <div className="flex items-center gap-6 text-sm">
              <Link
                href="/dashboard"
                className="text-gray-600 hover:text-black transition"
              >
                Dashboard
              </Link>

              <Link
                href="/profile"
                className="text-gray-600 hover:text-black transition"
              >
                Profile
              </Link>
            </div>
          )}

        </div>

        {/* RIGHT SIDE */}
        <div className="flex items-center gap-4 text-sm">

          {user ? (
            <button
              onClick={() => logout()}
              className="px-4 py-2 rounded-lg bg-black text-white hover:opacity-80 transition"
            >
              Logout
            </button>
          ) : (
            <>
              <Link
                href="/login"
                className="text-gray-600 hover:text-black transition"
              >
                Login
              </Link>

              <Link
                href="/register"
                className="px-4 py-2 rounded-lg bg-black text-white hover:opacity-80 transition"
              >
                Register
              </Link>
            </>
          )}

        </div>

      </div>

    </nav>
  );
}