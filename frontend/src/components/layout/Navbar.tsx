"use client";

import Link from "next/link";
import { useAuth } from "@/features/auth/hooks/useAuth";

export default function Navbar() {

  const { user, logout } = useAuth();

  return (
    <nav className="flex items-center justify-between bg-white px-6 py-4 shadow-sm">

      {/* LEFT SIDE */}
      <div className="flex items-center space-x-6">

        <Link
          href="/"
          className="text-lg font-semibold text-gray-800 hover:text-blue-600"
        >
          AI Exam Prep
        </Link>

        {user && (
          <>
            <Link
              href="/dashboard"
              className="text-gray-600 hover:text-blue-600"
            >
              Dashboard
            </Link>


            <Link
              href="/profile"
              className="text-gray-600 hover:text-blue-600"
            >
              Profile
            </Link>
          </>
        )}

      </div>

      {/* RIGHT SIDE */}
      <div className="flex items-center space-x-4">

        {user ? (
          <button
            onClick={() => logout()}
            className="rounded-md bg-red-500 px-4 py-2 text-white transition hover:bg-red-600"
          >
            Logout
          </button>
        ) : (
          <>
            <Link
              href="/login"
              className="text-gray-600 hover:text-blue-600"
            >
              Login
            </Link>

            <Link
              href="/register"
              className="rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
            >
              Register
            </Link>
          </>
        )}

      </div>

    </nav>
  );
}
