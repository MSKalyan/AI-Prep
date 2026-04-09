"use client";

import { useDashboardStats, useStudyPlan, usePerformance } from "@/features/analytics";
import { useAuth } from "@/features/auth";
import { apiClient } from "@/lib/apiClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect } from "react";
import { StatCard } from "@/features/analytics/components";

const services = [
  {
    name: "AI Service",
    description: "Ask AI questions powered by RAG",
    href: "/dashboard/ai_service",
  },
  {
    name: "Analytics",
    description: "View performance insights",
    href: "/dashboard/analytics",
  },
  {
    name: "Mock Tests",
    description: "Attempt and evaluate tests",
    href: "/dashboard/mocktest",
  },
];

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const { data, isLoading: statsLoading } = useDashboardStats(!!user);
  const { data: performanceData } = usePerformance();

  const activateMutation = useMutation({
    mutationFn: (id: number) => apiClient.post(`/roadmap/activate/${id}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
  });

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [user, isLoading, router]);

  if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  if (!user) return null;
  if (statsLoading || !data) return <div className="min-h-screen flex items-center justify-center">Loading dashboard...</div>;

  const performance = Array.isArray(performanceData?.topics) ? performanceData.topics : [];
  const weakTopics = performance.filter((t: any) => t.strength === "weak");

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-semibold">Dashboard</h1>
            <p className="text-sm text-gray-500">Overview of your preparation</p>
          </div>

          <button
            onClick={() => router.push("/dashboard/roadmap")}
            className="px-5 py-2 bg-black text-white rounded-lg hover:opacity-90 transition"
          >
            Generate Roadmap
          </button>
        </div>

        {/* KPI CARDS */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Study Streak" value={`${data.study_streak} days`} />
          <StatCard title="Topics Completed" value={data.topics_completed} />
          <StatCard title="Progress" value={`${data.roadmap_progress}%`} />
          <StatCard title="Avg Score" value={`${data.average_score}%`} />
        </div>

        {/* MAIN GRID */}
        <div className="grid lg:grid-cols-3 gap-6">

          {/* LEFT SIDE */}
          <div className="lg:col-span-2 space-y-6">

            {/* CONTINUE */}
            {data.continue_studying && (
              <div className="bg-white rounded-2xl shadow p-6 flex justify-between items-center">
                <div>
                  <h2 className="font-semibold">Continue Studying</h2>
                  <p className="text-sm text-gray-500">
                    {data.continue_studying.topic_name}
                  </p>
                </div>

                <Link
                  href={`/dashboard/study/${data.continue_studying.topic_id}`}
                  className="bg-black text-white px-4 py-2 rounded-lg text-sm"
                >
                  Resume
                </Link>
              </div>
            )}

            {/* ROADMAPS */}
            <div className="bg-white rounded-2xl shadow">
              <div className="p-6 border-b">
                <h2 className="font-semibold">Your Roadmaps</h2>
              </div>

              <div className="divide-y">
                {data.roadmaps.map((roadmap: any) => (
                  <div key={roadmap.id} className="flex justify-between items-center p-4">
                    <div>
                      <p className="font-medium">{roadmap.exam_name}</p>
                      {roadmap.is_active && (
                        <span className="text-xs text-green-600">Active</span>
                      )}
                    </div>

                    {!roadmap.is_active && (
                      <button
                        onClick={() => activateMutation.mutate(roadmap.id)}
                        className="px-3 py-1 bg-black text-white rounded-lg text-sm"
                      >
                        Activate
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* RIGHT SIDE */}
          <div className="space-y-6">

            {/* WEAK TOPICS */}
            <div className="bg-white rounded-2xl shadow p-6">
              <h2 className="font-semibold mb-4">Weak Topics</h2>

              {weakTopics.length === 0 ? (
                <p className="text-sm text-gray-500">No weak topics</p>
              ) : (
                <div className="space-y-2">
                  {weakTopics.slice(0, 5).map((t: any) => (
                    <div
                      key={t.topic_id}
                      className="flex justify-between text-sm bg-gray-50 p-2 rounded"
                    >
                      <span>{t.topic_name}</span>
                      <span>{(t.accuracy * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* SERVICES */}
            <div className="bg-white rounded-2xl shadow p-6">
              <h2 className="font-semibold mb-4">Services</h2>

              <div className="space-y-2">
                {services.map((service) => (
                  <Link
                    key={service.name}
                    href={service.href}
                    className="block p-3 border rounded-lg hover:bg-gray-50"
                  >
                    <p className="font-medium text-sm">{service.name}</p>
                    <p className="text-xs text-gray-500">{service.description}</p>
                  </Link>
                ))}
              </div>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
}