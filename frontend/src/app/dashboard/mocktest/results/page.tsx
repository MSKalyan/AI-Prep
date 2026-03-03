"use client";

import { useResults } from "@/features/mocktest/hooks/useMockTest";

export default function ResultsPage() {

  const { data, isLoading } = useResults();

  if (isLoading) return <div className="p-6">Loading...</div>;
  if (!data) return <div className="p-6">No results found</div>;

  return (
    <div className="p-6 space-y-4">
      {data.map((result: any) => (
        <div key={result.id} className="border p-4 rounded">
          <p>Score: {result.score}</p>
        </div>
      ))}
    </div>
  );
}