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