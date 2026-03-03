import router from "next/dist/shared/lib/router/router";
import Link from "next/link";
import { ReactNode } from "react";

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen flex bg-gray-100">

      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md p-6 hidden md:block">
        <h2 className="text-2xl font-bold mb-8">Dashboard</h2>

        <nav className="space-y-4 text-sm">
          <Link href="/dashboard" className="block hover:text-blue-600">
            Overview
          </Link>
          <Link href="/dashboard/ai_service" className="block hover:text-blue-600">
            AI Service
          </Link>
          <Link href="/dashboard/analytics" className="block hover:text-blue-600">
            Analytics
          </Link>
          <Link href="/dashboard/mocktest" className="block hover:text-blue-600">
            Mock Tests
          </Link>
          <Link href="/dashboard/roadmap" className="block hover:text-blue-600">
            Roadmap
          </Link>
          <Link href="/dashboard/roadmaps" className="block hover:text-blue-600">
          My Roadmaps
        </Link>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        {children}
      </main>

    </div>
  );
}