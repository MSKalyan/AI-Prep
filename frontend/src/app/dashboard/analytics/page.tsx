"use client";

import { usePerformance, useAnalyticsSummary } from "@/features/analytics/hooks/hooks";
import { TopicPerformance } from "@/features/analytics/services/analytics.services";

/* ================= PAGE ================= */

export default function AnalyticsPage() {
  const { data, isLoading } = usePerformance();
    const topics=data?.topics||[];

  const { data: summary } = useAnalyticsSummary();
  if (isLoading) {
    return <div className="p-6 text-center">Loading analytics...</div>;
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
    <div className="p-6 space-y-8">
      <h1 className="text-3xl font-bold">Analytics</h1>

      {/* ================= SUMMARY ================= */}
      <div className="grid md:grid-cols-4 gap-4">
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
        title="🔴 Weak Topics (Focus Here)"
        data={weak}
        color="bg-red-100"
        emptyText="No weak topics — good progress"
      />

      <Section
        title="🟡 Needs Improvement"
        data={moderate}
        color="bg-yellow-100"
        emptyText="No moderate topics"
      />

      <Section
        title="🟢 Strong Areas"
        data={strong}
        color="bg-green-100"
        emptyText="No strong topics yet"
      />
    </div>
  );
}

/* ================= SECTION ================= */

function Section({
  title,
  data,
  color,
  emptyText,
}: {
  title: string;
  data: TopicPerformance[];
  color: string;
  emptyText: string;
}) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-3">{title}</h2>

      {data.length === 0 ? (
        <p className="text-gray-500">{emptyText}</p>
      ) : (
        <div className="grid md:grid-cols-3 gap-4">
          {data.map((t) => (
            <div
              key={t.topic_id}
              className={`p-4 rounded shadow-sm ${color}`}
            >
              <p className="font-medium">
                {t.topic_name || `Topic ${t.topic_id}`}
              </p>

              <p className="text-sm text-gray-700">
                Accuracy: {(t.accuracy * 100).toFixed(1)}%
              </p>

              <p className="text-sm text-gray-700">
                Avg Time: {t.avg_time}s
              </p>

              <p className="text-sm text-gray-700">
                Attempts: {t.total_attempts}
              </p>
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
    <div className="bg-white p-4 rounded shadow-sm">
      <p className="text-sm text-gray-500">{title}</p>
      <h2 className="text-xl font-semibold">{value}</h2>
    </div>
  );
}