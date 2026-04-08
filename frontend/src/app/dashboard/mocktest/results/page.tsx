"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getResults } from "@/features/mocktest/services/mocktest.services";

export default function ResultsPage() {

  const router = useRouter();

  const { data, isLoading } = useQuery({
    queryKey: ["results"],
    queryFn: getResults,
  });

  if (isLoading) return <div className="px-4 sm:px-6 py-6">Loading...</div>;

  if (!data || data.length === 0) {
    return (
      <div className="px-4 sm:px-6 py-6 space-y-4">

        {/* ✅ Navigation */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => router.push("/dashboard/")}
            className="px-3 py-1.5 border rounded text-sm sm:text-base"
          >
            ← Back
          </button>

          <button
            onClick={() => router.push("/dashboard")}
            className="px-3 py-1.5 bg-gray-200 rounded text-sm sm:text-base"
          >
            Dashboard
          </button>

          <button
            onClick={() => router.push("/dashboard/roadmap")}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm sm:text-base"
          >
            Back to Study
          </button>
        </div>

        <div className="text-sm text-gray-600">No results found</div>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 py-6 space-y-4">

      {/* ✅ Navigation */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={() => router.back()}
          className="px-3 py-1.5 border rounded text-sm sm:text-base"
        >
          ← Back
        </button>

        <button
          onClick={() => router.push("/dashboard")}
          className="px-3 py-1.5 bg-gray-200 rounded text-sm sm:text-base"
        >
          Dashboard
        </button>

        
      </div>

      <h2 className="text-xl font-semibold">Your Mock Tests</h2>

      {data.map((result: any) => (
        <div
  key={result.attempt_id}
  onClick={() =>
    router.push(`/dashboard/mocktest/results/${result.attempt_id}`)
  }
  className="border p-4 rounded cursor-pointer hover:bg-gray-100"
>
  {/* SUBJECT */}
  {result.subject && (
    <div className="text-xs text-gray-500">
      {result.subject}
    </div>
  )}

  {/* TOPIC / TITLE */}
  <div className="font-semibold text-gray-800">
    {result.topic || result.title || "Mock Test"}
  </div>

  {/* DATE */}
  <div className="text-xs text-gray-400 mb-2">
    {new Date(result.date).toLocaleDateString()}
  </div>

  {/* STATS */}
  <div className="flex flex-col sm:flex-row sm:items-center gap-2 text-xs sm:text-sm">
    <span className="flex-1"><b>Score:</b> {result.score}</span>
    <span className="text-right"><b>{result.percentage}%</b></span>
  </div>
</div>
      ))}

    </div>
  );
}