"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { explainQuestion, getResultDetail } from "@/features/mocktest/services/mocktest.services";
import { useState } from "react";

export default function ResultDetailPage() {

  const params = useParams();
  const router = useRouter();
const [aiExplanations, setAiExplanations] = useState<Record<number, string>>({});
const [loadingExplain, setLoadingExplain] = useState<number | null>(null);
  // ✅ SAFE PARAM PARSING
  const rawId = params?.id;
  const attemptId =
    typeof rawId === "string"
      ? Number(rawId)
      : Array.isArray(rawId)
      ? Number(rawId[0])
      : null;

      const handleExplain = async (questionId: number) => {
  try {
    setLoadingExplain(questionId);

    const res = await explainQuestion(questionId);

    setAiExplanations(prev => ({
      ...prev,
      [questionId]: res.explanation
    }));

  } catch (err) {
    alert("Failed to generate explanation");
  } finally {
    setLoadingExplain(null);
  }
};
      
  // ✅ INVALID CASE
  if (!attemptId) {
    return (
      <div className="p-6 space-y-4">
        <p className="text-red-600">Invalid result page</p>

        <button
          onClick={() => router.replace("/dashboard/mocktest/results")}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Go to Results List
        </button>
      </div>
    );
  }

  const { data, isLoading } = useQuery({
    queryKey: ["result-detail", attemptId],
    queryFn: () => getResultDetail(attemptId),
    enabled: !!attemptId,
  });
  

  if (isLoading) return <div className="p-6">Loading...</div>;
  if (!data) return <div className="p-6">No data</div>;

  return (
    <div className="p-6 space-y-6">

      {/* ✅ NAVIGATION */}
      <div className="flex gap-3">
        <button
          onClick={() => router.back()}
          className="px-3 py-1.5 border rounded"
        >
          ← Back
        </button>

        {/* ✅ FIXED */}
        <button
          onClick={() => router.push("/dashboard/mocktest/results")}
          className="px-3 py-1.5 bg-gray-200 rounded"
        >
          All Results
        </button>

        <button
          onClick={() => router.push("/dashboard/roadmap")}
          className="px-3 py-1.5 bg-blue-600 text-white rounded"
        >
          Back to Study
        </button>
      </div>

      {/* ✅ SUMMARY */}
      <div className="border p-4 rounded bg-gray-50">
        <h2 className="text-xl font-semibold">Test Summary</h2>

        <p>Score: {data.score} / {data.total_marks}</p>
        <p>Percentage: {data.percentage?.toFixed(2)}%</p>
        <p>Correct: {data.correct}</p>
        <p>Incorrect: {data.incorrect}</p>
        <p>Unanswered: {data.unanswered}</p>
        <p>Time: {data.time_taken} mins</p>
      </div>

      {/* ✅ QUESTIONS REVIEW */}
      <div className="space-y-4">
        {data.questions.map((q: any, index: number) => (
          <div key={q.question_id} className="border p-4 rounded">

            <p className="font-medium">
              Q{index + 1}. {q.question_text}
            </p>

            {/* Options */}
            <div className="mt-2 space-y-1">
              {Object.entries(q.options).map(([key, text]: any) => (
                <div
                  key={key}
                  className={`p-2 rounded
                    ${q.correct_answer === key ? "bg-green-200" : ""}
                    ${q.your_answer === key && q.your_answer !== q.correct_answer ? "bg-red-200" : ""}
                  `}
                >
                  {key}. {text}
                </div>
              ))}
            </div>

            <p className="mt-2">
              Your Answer: <b>{q.your_answer || "Not answered"}</b>
            </p>

            <p>
              Correct Answer: <b>{q.correct_answer}</b>
            </p>

            <p>
              Marks: {q.marks_obtained}
            </p>

            {/* DB Explanation */}
            {q.explanation && (
              <div className="mt-2 text-sm text-gray-700">
                Explanation: {q.explanation}
              </div>
            )}

            {/* 🔥 AI Explain Placeholder */}
           <button
  onClick={() => handleExplain(q.question_id)}
  className="mt-2 text-blue-600 underline"
>
  {loadingExplain === q.question_id ? "Generating..." : "Explain with AI"}
</button>
{aiExplanations[q.question_id] && (
  <div className="mt-2 p-3 bg-blue-50 rounded text-sm">
    {aiExplanations[q.question_id]}
  </div>
)}

          </div>
        ))}
      </div>

    </div>
  );
}