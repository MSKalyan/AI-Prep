"use client";

import { useDashboardStats, useStudyPlan, usePerformance } from "@/features/analytics/hooks/hooks";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { apiClient } from "@/lib/apiClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect } from "react";

const services = [
  {
    name: "AI Service",
    description: "Ask AI questions powered by RAG and conversation history.",
    href: "/dashboard/ai_service",
  },
  {
    name: "Analytics",
    description: "View weak topics, accuracy trends, and performance insights.",
    href: "/dashboard/analytics",
  },
  {
    name: "Mock Tests",
    description: "Attempt mock exams and evaluate your performance.",
    href: "/dashboard/mocktest",
  },
];

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const { data, isLoading: statsLoading } = useDashboardStats(!!user);
  const { data: studyPlan = [] } = useStudyPlan();
  const { data: performanceData } = usePerformance();

  const activateMutation = useMutation({
    mutationFn: (id: number) =>
      apiClient.post(`/roadmap/activate/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading) return <div className="p-10 text-center">Loading...</div>;

  if (!user) return null;

  if (statsLoading || !data) {
    return <div className="p-10 text-center">Loading dashboard...</div>;
  }

  const performance = Array.isArray(performanceData?.topics)
    ? performanceData.topics
    : [];

  const weakTopics = performance.filter((t: any) => t.strength === "weak");

  function activateRoadmap(id: number) {
    activateMutation.mutate(id);
  }

  return (
<div className="w-full h-full px-4 sm:px-6 py-6 sm:py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8 sm:space-y-12">

        {/* HEADER */}
        <div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            Overview of your progress and activity
          </p>
        </div>

        {/* ================= STATS ================= */}
        <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Study Streak" value={`${data.study_streak} days`} />
          <StatCard title="Topics Completed" value={data.topics_completed} />
          <StatCard title="Roadmap Progress" value={`${data.roadmap_progress}%`} />
          <StatCard title="Average Score" value={`${data.average_score}%`} />
        </div>

        {/* ================= WEAK TOPICS ================= */}
        {weakTopics.length > 0 && (
          <div className="border border-gray-200 rounded-2xl p-4 sm:p-6">

            <h2 className="text-base sm:text-lg font-semibold mb-4">Weak Topics</h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
              {weakTopics.slice(0, 6).map((t: any) => (
                <div
                  key={t.topic_id}
                  className="flex justify-between bg-gray-50 p-3 rounded-lg text-sm"
                >
                  <span className="truncate">
                    {t.topic_name || `Topic ${t.topic_id}`}
                  </span>

                  <span className="text-xs sm:text-sm text-gray-500 ml-2">
                    {(t.accuracy * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>

          </div>
        )}

        {/* ================= CONTINUE ================= */}
        {data.continue_studying && (
          <div className="border border-gray-200 rounded-2xl p-4 sm:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">

            <div>
              <h2 className="font-semibold text-base sm:text-lg">Continue Studying</h2>
              <p className="text-gray-600 text-xs sm:text-sm">
                {data.continue_studying.topic_name}
              </p>
            </div>

            <Link
              href={`/dashboard/study/${data.continue_studying.topic_id}`}
              className="bg-black text-white px-4 py-2 rounded-lg hover:opacity-80 transition text-sm sm:text-base whitespace-nowrap w-full sm:w-auto text-center"
            >
              Resume
            </Link>

          </div>
        )}

        {/* ================= ROADMAPS ================= */}
        <div>
          <h2 className="text-lg sm:text-xl font-semibold mb-4">Your Roadmaps</h2>

          <div className="border border-gray-200 rounded-2xl divide-y">
            {data.roadmaps.map((roadmap: any) => (
              <div key={roadmap.id} className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-3 sm:p-4 gap-3 sm:gap-0">

                <div>
                  <span className="font-medium text-sm sm:text-base">{roadmap.exam_name}</span>
                  {roadmap.is_active && (
                    <p className="text-xs text-gray-500">Active</p>
                  )}
                </div>

                {!roadmap.is_active && (
                  <button
                    onClick={() => activateRoadmap(roadmap.id)}
                    className="bg-black text-white px-3 py-1 rounded-lg hover:opacity-80 transition text-sm w-full sm:w-auto"
                  >
                    Activate
                  </button>
                )}

              </div>
            ))}
          </div>
        </div>

        {/* ================= SERVICES ================= */}
        <div>
          <h2 className="text-lg sm:text-xl font-semibold mb-4">Platform Services</h2>

          <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {services.map((service) => (
              <Link
                key={service.name}
                href={service.href}
                className="border border-gray-200 rounded-2xl p-4 sm:p-6 hover:shadow-md hover:-translate-y-1 transition"
              >
                <h3 className="font-semibold text-base sm:text-lg">{service.name}</h3>
                <p className="text-xs sm:text-sm text-gray-500 mt-1">
                  {service.description}
                </p>
              </Link>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

function StatCard({ title, value }: any) {
  return (
    <div className="border border-gray-200 rounded-2xl p-4 sm:p-6 hover:shadow-md transition">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{title}</p>
      <h2 className="text-xl sm:text-2xl font-semibold mt-1">{value}</h2>
    </div>
  );
}