"use client";

import { useDashboardStats, useStudyPlan, usePerformance } from "@/features/analytics/hooks/hooks";
import { apiClient } from "@/lib/apiClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

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
    name: "Study Plan",
    description: "Adaptive plan based on your weak areas and priorities.",
    href: "/dashboard/study-plan",
  },
  {
    name: "Mock Tests",
    description: "Attempt mock exams and evaluate your performance.",
    href: "/dashboard/mocktest",
  },
];

export default function DashboardPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useDashboardStats();
  const { data: studyPlan = [] } = useStudyPlan();
  const { data: performance = [] } = usePerformance();

  const weakTopics = performance.filter((t: any) => t.strength === "weak");

  const activateMutation = useMutation({
    mutationFn: (id: number) =>
      apiClient.post(`/roadmap/activate/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  function activateRoadmap(id: number) {
    activateMutation.mutate(id);
  }

  if (isLoading || !data) {
    return <div className="p-10 text-center">Loading dashboard...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 px-6 py-8">
      <div className="max-w-7xl mx-auto space-y-10">

        <h1 className="text-3xl font-bold">Dashboard</h1>

        {/* ================= STATS ================= */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Study Streak" value={`${data.study_streak} days`} />
          <StatCard title="Topics Completed" value={data.topics_completed} />
          <StatCard title="Roadmap Progress" value={`${data.roadmap_progress}%`} />
          <StatCard title="Average Score" value={`${data.average_score}%`} />
        </div>

        {/* ================= STUDY PLAN CTA ================= */}
        <div className="bg-blue-600 text-white p-6 rounded-xl flex justify-between items-center shadow">
          <div>
            <h2 className="text-lg font-semibold">
              Your Personalized Study Plan
            </h2>
            <p className="text-sm opacity-90">
              Focus on your weak topics and improve faster
            </p>
          </div>

          <Link
            href="/dashboard/study-plan"
            className="bg-white text-blue-600 px-4 py-2 rounded-lg font-medium"
          >
            View Plan →
          </Link>
        </div>



        {/* ================= WEAK TOPICS ================= */}
        {weakTopics.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 shadow-sm">

            <h2 className="text-lg font-semibold mb-3">
              ⚠ Weak Topics
            </h2>

            <div className="grid md:grid-cols-2 gap-4">
              {weakTopics.slice(0, 6).map((t: any) => (
                <div
                  key={t.topic_id}
                  className="flex justify-between bg-white p-3 rounded"
                >
                  <span>
                    {t.topic_name || `Topic ${t.topic_id}`}
                  </span>

                  <span className="text-sm text-gray-600">
                    {(t.accuracy * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>

          </div>
        )}

        {/* ================= CONTINUE ================= */}
        {data.continue_studying && (
          <div className="bg-white rounded-xl p-6 shadow-sm flex justify-between items-center">

            <div>
              <h2 className="font-semibold">Continue Studying</h2>
              <p>{data.continue_studying.topic_name}</p>
            </div>

            <Link
              href={`/dashboard/study/${data.continue_studying.topic_id}`}
              className="bg-blue-600 text-white px-4 py-2 rounded"
            >
              Resume
            </Link>

          </div>
        )}

        {/* ================= ROADMAPS ================= */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Your Roadmaps</h2>

          <div className="bg-white rounded-xl shadow-sm divide-y">
            {data.roadmaps.map((roadmap: any) => (
              <div key={roadmap.id} className="flex justify-between p-4">

                <div>
                  <span>{roadmap.exam_name}</span>
                  {roadmap.is_active && (
                    <p className="text-green-600 text-sm">Active</p>
                  )}
                </div>

                {!roadmap.is_active && (
                  <button
                    onClick={() => activateRoadmap(roadmap.id)}
                    className="bg-blue-600 text-white px-3 py-1 rounded"
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
          <h2 className="text-xl font-semibold mb-4">Platform Services</h2>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {services.map((service) => (
              <Link
                key={service.name}
                href={service.href}
                className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition"
              >
                <h3 className="font-semibold">{service.name}</h3>
                <p className="text-sm text-gray-600">
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
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <p className="text-sm text-gray-500">{title}</p>
      <h2 className="text-xl font-semibold">{value}</h2>
    </div>
  );
}