"use client";

import { usePerformance, useAnalyticsSummary } from "@/features/analytics/hooks/hooks";
import { TopicPerformance } from "@/features/analytics/services/analytics.services";

/* ================= PAGE ================= */

export default function AnalyticsPage() {
  const { data, isLoading } = usePerformance();
  const topics = data?.topics || [];

  const { data: summary } = useAnalyticsSummary();

  if (isLoading) {
    return <div className="p-10 text-center text-gray-500">Loading analytics...</div>;
  }

  // ---------------- SUMMARY DATA ----------------
  const totalMocktests = summary?.total_mocktests || 0;
  const totalQuestions = summary?.total_questions_attempted || 0;

  // ---------------- CLASSIFICATION ----------------
  const weak = topics.filter((t) => t.strength === "weak");
  const moderate = topics.filter((t) => t.strength === "moderate");
  const strong = topics.filter((t) => t.strength === "strong");

  // ---------------- BASIC METRICS ----------------
  const totalTopics = topics.length;

  const avgAccuracy =
    totalTopics > 0
      ? topics.reduce((s, t) => s + t.accuracy, 0) / totalTopics
      : 0;

  const avgTime =
    totalTopics > 0
      ? topics.reduce((s, t) => s + t.avg_time, 0) / totalTopics
      : 0;

  return (
    <div className="min-h-screen bg-white text-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8 sm:space-y-12">

        {/* HEADER */}
        <div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight">Analytics</h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            Track your performance, accuracy, and weak areas
          </p>
        </div>

        {/* ================= SUMMARY ================= */}
        <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Mock Tests Attempted" value={totalMocktests} />
          <StatCard title="Questions Attempted" value={totalQuestions} />
          <StatCard
            title="Avg Accuracy"
            value={`${(avgAccuracy * 100).toFixed(1)}%`}
          />
          <StatCard
            title="Avg Time / Question"
            value={`${avgTime.toFixed(1)} sec`}
          />
        </div>

        {/* ================= SECTIONS ================= */}
        <Section
          title="Weak Topics"
          data={weak}
          emptyText="No weak topics — good progress"
        />

  

      </div>
    </div>
  );
}

/* ================= SECTION ================= */

function Section({
  title,
  data,
  emptyText,
}: {
  title: string;
  data: TopicPerformance[];
  emptyText: string;
}) {
  return (
    <div>
      <h2 className="text-base sm:text-lg md:text-xl font-semibold mb-4">{title}</h2>

      {data.length === 0 ? (
        <p className="text-xs sm:text-sm text-gray-500">{emptyText}</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {data.map((t) => (
            <div
              key={t.topic_id}
              className="border border-gray-200 rounded-2xl p-4 sm:p-5 hover:shadow-md transition"
            >
              <p className="font-medium text-sm sm:text-base mb-2">
                {t.topic_name || `Topic ${t.topic_id}`}
              </p>

              <div className="space-y-1 text-xs sm:text-sm text-gray-600">
                <p>Accuracy: {(t.accuracy * 100).toFixed(1)}%</p>
                <p>Avg Time: {t.avg_time}s</p>
                <p>Attempts: {t.total_attempts}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ================= SUMMARY CARD ================= */

function StatCard({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) {
  return (
    <div className="border border-gray-200 rounded-2xl p-4 sm:p-5 hover:shadow-md transition">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{title}</p>
      <h2 className="text-lg sm:text-2xl font-semibold mt-1">{value}</h2>
    </div>
  );
}