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
      className={`block px-4 py-2.5 rounded-lg text-sm transition ${
        pathname === href
          ? "bg-black text-white font-medium"
          : "text-gray-600 hover:bg-gray-100"
      }`}
    >
      {label}
    </Link>
  );

  return (
<div className="min-h-screen flex flex-col md:flex-row bg-white text-black">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 hidden md:flex flex-col">

        {/* Logo / Title */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold tracking-tight">
            AI Exam Prep
          </h2>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">

          {navItem("/dashboard", "Overview")}
          {navItem("/dashboard/ai_service", "AI Tutor")}
          {navItem("/dashboard/analytics", "Analytics")}
          {navItem("/dashboard/mocktest/results", "Mock Tests")}
          {navItem("/dashboard/roadmap", "Generate Roadmap")}
          {navItem("/dashboard/roadmaps", "My Roadmaps")}

        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
          AI Exam Platform
        </div>

      </aside>

      {/* Mobile nav */}
      <div className="md:hidden w-full border-b border-gray-200 bg-white">
        <nav className="flex overflow-x-auto gap-2 px-4 py-3">
          <Link
            href="/dashboard"
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition ${pathname === "/dashboard" ? "bg-black text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
          >
            Overview
          </Link>
          <Link
            href="/dashboard/ai_service"
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition ${pathname === "/dashboard/ai_service" ? "bg-black text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
          >
            AI Tutor
          </Link>
          <Link
            href="/dashboard/analytics"
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition ${pathname === "/dashboard/analytics" ? "bg-black text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
          >
            Analytics
          </Link>
          <Link
            href="/dashboard/mocktest/results"
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition ${pathname === "/dashboard/mocktest/results" ? "bg-black text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
          >
            Mock Tests
          </Link>
          <Link
            href="/dashboard/roadmap"
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition ${pathname === "/dashboard/roadmap" ? "bg-black text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
          >
            Roadmap
          </Link>
          <Link
            href="/dashboard/roadmaps"
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition ${pathname === "/dashboard/roadmaps" ? "bg-black text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
          >
            My Roadmaps
          </Link>
        </nav>
      </div>

      {/* Content Area */}
      <div className="flex-1 flex flex-col">

        {/* Optional Header (clean version if needed later) */}
        {/* 
        <header className="border-b border-gray-200 px-8 py-4 flex items-center justify-between">
          <h1 className="text-sm font-medium text-gray-600">
            Dashboard
          </h1>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">Welcome</span>
            <button className="text-sm text-black hover:opacity-70">
              Logout
            </button>
          </div>
        </header> 
        */}

        {/* Main Content */}
        <main className="flex-1 px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10 overflow-y-auto">
          {children}
        </main>

      </div>

    </div>
  );
}