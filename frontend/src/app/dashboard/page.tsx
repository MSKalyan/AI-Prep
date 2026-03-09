"use client";

import { apiClient } from "@/lib/apiClient";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

const services = [
  {
    name: "AI Service",
    description: "Ask AI questions powered by RAG and conversation history.",
    href: "/dashboard/ai_service",
  },
  {
    name: "Analytics",
    description: "View performance metrics and exam insights.",
    href: "/dashboard/analytics",
  },
  {
    name: "Mock Tests",
    description: "Attempt mock exams and evaluate your performance.",
    href: "/dashboard/mocktest",
  },
  {
    name: "Roadmap",
    description: "Generate and track your personalized exam roadmap.",
    href: "/dashboard/roadmap",
  },
];

export default function DashboardPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const res = await apiClient.get("/analytics/dashboard/");
      return res.data;
    },
  });

  const activateMutation = useMutation({
    mutationFn: (id: number) => apiClient.post(`/roadmap/activate/${id}/`),
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

        {/* Stats */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">

          <StatCard
            title="Study Streak"
            value={`${data.study_streak} days`}
          />

          <StatCard
            title="Topics Completed"
            value={data.topics_completed}
          />

          <StatCard
            title="Roadmap Progress"
            value={`${data.roadmap_progress}%`}
          />

          <StatCard
            title="Average Score"
            value={`${data.average_score}%`}
          />

          {data.weak_subject && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 shadow-sm">
              <p className="text-sm text-red-500">Weak Subject</p>

              <h2 className="text-lg font-semibold truncate">
                {data.weak_subject.subject}
              </h2>

              <p className="text-sm text-gray-600">
                Accuracy: {data.weak_subject.accuracy}%
              </p>
            </div>
          )}
        </div>

        {/* Continue Studying */}
        {data.continue_studying && (
          <div className="bg-white rounded-xl p-6 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">

            <div>
              <h2 className="text-lg font-semibold">
                Continue Studying
              </h2>

              <p className="text-gray-600 truncate max-w-lg">
                {data.continue_studying.topic_name}
              </p>
            </div>

            <Link
              href={`/dashboard/study/${data.continue_studying.topic_id}`}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Resume
            </Link>

          </div>
        )}

        {/* Roadmaps */}
        <div>

          <h2 className="text-xl font-semibold mb-4">
            Your Roadmaps
          </h2>

          <div className="bg-white rounded-xl shadow-sm divide-y">

            {data.roadmaps.map((roadmap: any) => (
              <div
                key={roadmap.id}
                className="flex items-center justify-between p-4"
              >

                <div className="flex flex-col min-w-0">
                  <span className="font-medium truncate max-w-xs">
                    {roadmap.exam_name}
                  </span>

                  {roadmap.is_active && (
                    <span className="text-green-600 text-sm">
                      Active
                    </span>
                  )}
                </div>

                {!roadmap.is_active && (
                  <button
                    onClick={() => activateRoadmap(roadmap.id)}
                    className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 transition"
                  >
                    Activate
                  </button>
                )}

              </div>
            ))}

          </div>
        </div>

        {/* Services */}
        <div>

          <h2 className="text-xl font-semibold mb-4">
            Platform Services
          </h2>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">

            {services.map((service) => (
              <Link
                key={service.name}
                href={service.href}
                className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition flex flex-col"
              >

                <h3 className="text-lg font-semibold mb-2">
                  {service.name}
                </h3>

                <p className="text-sm text-gray-600 line-clamp-3">
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
      <h2 className="text-2xl font-semibold mt-1 truncate">{value}</h2>
    </div>
  );
}