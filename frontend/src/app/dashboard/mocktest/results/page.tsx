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

  if (isLoading) return <div className="p-6">Loading...</div>;

  if (!data || data.length === 0) {
    return (
      <div className="p-6 space-y-4">

        {/* ✅ Navigation */}
        <div className="flex gap-3">
          <button
            onClick={() => router.back()}
            className="px-3 py-1.5 border rounded"
          >
            ← Back
          </button>

          <button
            onClick={() => router.push("/dashboard")}
            className="px-3 py-1.5 bg-gray-200 rounded"
          >
            Dashboard
          </button>

          <button
            onClick={() => router.push("/dashboard/roadmap")}
            className="px-3 py-1.5 bg-blue-600 text-white rounded"
          >
            Back to Study
          </button>
        </div>

        <div>No results found</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">

      {/* ✅ Navigation */}
      <div className="flex gap-3">
        <button
          onClick={() => router.back()}
          className="px-3 py-1.5 border rounded"
        >
          ← Back
        </button>

        <button
          onClick={() => router.push("/dashboard")}
          className="px-3 py-1.5 bg-gray-200 rounded"
        >
          Dashboard
        </button>

        <button
          onClick={() => router.push("/dashboard/roadmap")}
          className="px-3 py-1.5 bg-blue-600 text-white rounded"
        >
          Back to Study
        </button>
        <button
  onClick={() => router.push("/dashboard/mocktest")}
  className="px-3 py-1.5 bg-green-600 text-white rounded"
>
  Take New Test
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
          <p><b>Score:</b> {result.score}</p>
          <p><b>Percentage:</b> {result.percentage}%</p>
        </div>
      ))}

    </div>
  );
}