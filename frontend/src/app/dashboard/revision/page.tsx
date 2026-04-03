"use client";

import { useTodayPlan } from "@/features/analytics/hooks/hooks";

export default function StudyPlanPage() {
  const { data, isLoading } = useTodayPlan();

  if (isLoading) {
    return <div className="p-6 text-center">Loading today’s plan...</div>;
  }

  if (!data) {
    return <div className="p-6 text-center text-gray-500">No plan available</div>;
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">

      {/* HEADER */}
      <div>
        <h1 className="text-2xl font-bold">Today's Study Plan</h1>
        <p className="text-sm text-gray-500">
          Week {data.week} • Day {data.day}
        </p>
      </div>

      {/* LEARN SECTION */}
      <div className="bg-white p-5 rounded-xl shadow-sm border">
        <p className="text-blue-600 font-semibold mb-2">
          📘 Learn Topics
        </p>

        {data.learn_topics?.length > 0 ? (
          <ul className="list-disc ml-5 text-gray-700">
            {data.learn_topics.map((topic: any) => (
              <li key={topic.topic_id}>{topic.topic_name}</li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-400 text-sm">No topics for today</p>
        )}
      </div>

      {/* REVISION SECTION */}
      {data.revision && (
        <div className="bg-red-50 border border-red-200 p-5 rounded-xl">
          <p className="text-red-600 font-semibold mb-2">
            🔁 Focus Revision
          </p>

          <p className="text-gray-800">
            {data.revision.topic_name}
          </p>

          <p className="text-xs text-gray-500 mt-1">
            Priority: {(data.revision.priority * 100).toFixed(0)}%
          </p>
        </div>
      )}

      {/* ACTION BUTTON */}
      <div className="pt-2">
        <button className="w-full bg-black text-white py-2 rounded-lg hover:opacity-90">
          Mark Day as Completed
        </button>
      </div>

    </div>
  );
}