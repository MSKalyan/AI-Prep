"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { usePathname } from "next/navigation";

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();

  const navItem = (href: string, label: string) => (
    <Link
      href={href}
      className={`block px-3 py-2 rounded-md transition ${
        pathname === href
          ? "bg-blue-100 text-blue-700 font-medium"
          : "text-gray-700 hover:bg-gray-100"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <div className="min-h-screen flex bg-gray-100">

      {/* Sidebar */}
      <aside className="w-64 bg-white border-r hidden md:flex flex-col">

        <div className="p-6 border-b">
          <h2 className="text-xl font-bold">AI Exam Prep</h2>
        </div>

        <nav className="flex-1 p-4 space-y-2 text-sm">

          {navItem("/dashboard", "Overview")}
          {navItem("/dashboard/ai_service", "AI Tutor")}
          {navItem("/dashboard/analytics", "Analytics")}
          {navItem("/dashboard/mocktest", "Mock Tests")}
          {navItem("/dashboard/roadmap", "Roadmap")}
          {navItem("/dashboard/roadmaps", "My Roadmaps")}

        </nav>

        <div className="p-4 border-t text-sm text-gray-500">
          AI Exam Platform
        </div>

      </aside>

      {/* Content Area */}
      <div className="flex-1 flex flex-col">

        {/* Top Header
        <header className="bg-white border-b px-8 py-4 flex items-center justify-between">

          <h1 className="text-lg font-semibold">
            Dashboard
          </h1>

          <div className="flex items-center gap-4">

            <span className="text-sm text-gray-600">
              Welcome
            </span>

            <button className="text-sm text-red-600 hover:underline">
              Logout
            </button>

          </div>

        </header> */}

        {/* Main Page Content */}
        <main className="flex-1 p-8 overflow-y-auto">
          {children}
        </main>

      </div>

    </div>
  );
}