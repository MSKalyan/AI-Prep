'use client';

import { useRouter } from 'next/navigation';
import { useResults } from '@/features/mocktest';

interface MockTestResult {
  attempt_id: number;
  subject?: string;
  topic?: string;
  title?: string;
  percentage: number;
  score: number;
  date: string;
}

export default function ResultsPageImproved() {
  const router = useRouter();
  const { data, isLoading } = useResults();

  if (isLoading) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">Your Mock Tests</h1>

        <div className="flex gap-3">
          <button onClick={() => router.back()} className="px-4 py-2 border rounded-lg">
            Back
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-black text-white rounded-lg"
          >
            Dashboard
          </button>
        </div>
      </div>

      {/* EMPTY STATE */}
      {!data || data.length === 0 ? (
        <div className="bg-white rounded-2xl shadow p-8 text-center">
          <p className="text-gray-600 mb-4">No mock tests attempted yet</p>
          <button
            onClick={() => router.push('/dashboard/roadmap')}
            className="px-6 py-2 bg-black text-white rounded-lg"
          >
            Start Practicing
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {data.map((result: MockTestResult) => {
            const isGood = result.percentage >= 60;

            return (
              <button
                key={result.attempt_id}
                type="button"
                onClick={() => router.push(`/dashboard/mocktest/results/${result.attempt_id}`)}
                className="bg-white rounded-2xl shadow p-5 cursor-pointer hover:shadow-md transition w-full text-left"
              >
                {/* TOP */}
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs text-gray-500">{result.subject || 'General'}</p>
                    <h2 className="font-semibold text-gray-800">
                      {result.topic || result.title || 'Mock Test'}
                    </h2>
                  </div>

                  <span
                    className={`text-sm px-3 py-1 rounded ${
                      isGood ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {result.percentage}%
                  </span>
                </div>

                {/* DATE */}
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(result.date).toLocaleDateString()}
                </p>

                {/* PROGRESS BAR */}
                <div className="mt-3">
                  <div className="w-full bg-gray-200 h-2 rounded">
                    <div
                      className={`h-2 rounded ${isGood ? 'bg-green-500' : 'bg-red-500'}`}
                      style={{ width: `${result.percentage}%` }}
                    />
                  </div>
                </div>

                {/* FOOTER STATS */}
                <div className="flex justify-between mt-3 text-sm text-gray-600">
                  <span>Score: {result.score}</span>
                  <span>View Details →</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
