"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getResultDetail } from "@/features/mocktest/services";
import { useAttemptId, useAIExplanation } from "@/features/mocktest";

export default function ResultDetailPageImproved() {
  const attemptId = useAttemptId();
  const router = useRouter();

  const { aiExplanations, loadingExplain, handleExplain } = useAIExplanation();

  if (!attemptId) {
    return (
      <div className="p-6">
        <p className="text-red-600 mb-4">Invalid result page</p>
        <button
          onClick={() => router.replace("/dashboard/mocktest/results")}
          className="px-4 py-2 bg-black text-white rounded-lg"
        >
          Go to Results
        </button>
      </div>
    );
  }

  const { data, isLoading } = useQuery({
    queryKey: ["result-detail", attemptId],
    queryFn: () => getResultDetail(attemptId),
    enabled: !!attemptId,
  });

  if (isLoading || !data) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">Test Result</h1>

        <div className="flex gap-3">
        
          <button
            onClick={() => router.push("/dashboard/mocktest/results")}
            className="px-4 py-2 bg-black text-white rounded-lg"
          >
            All Results
          </button>
        </div>
      </div>

      {/* SUMMARY CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-2xl shadow">
          <p className="text-sm text-gray-500">Score</p>
          <p className="text-xl font-semibold">{data.score}/{data.total_marks}</p>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow">
          <p className="text-sm text-gray-500">Percentage</p>
          <p className="text-xl font-semibold">{data.percentage?.toFixed(2)}%</p>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow">
          <p className="text-sm text-gray-500">Accuracy</p>
          <p className="text-xl font-semibold">
            {((data.correct / (data.correct + data.incorrect || 1)) * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow">
          <p className="text-sm text-gray-500">Time</p>
          <p className="text-xl font-semibold">{data.time_taken} mins</p>
        </div>
      </div>

      {/* PERFORMANCE BAR */}
      <div className="bg-white p-4 rounded-2xl shadow mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span>Correct: {data.correct}</span>
          <span>Incorrect: {data.incorrect}</span>
          <span>Unanswered: {data.unanswered}</span>
        </div>

        <div className="flex h-3 rounded overflow-hidden">
          <div
            className="bg-green-500"
            style={{ width: `${(data.correct / data.questions.length) * 100}%` }}
          />
          <div
            className="bg-red-500"
            style={{ width: `${(data.incorrect / data.questions.length) * 100}%` }}
          />
          <div
            className="bg-gray-300"
            style={{ width: `${(data.unanswered / data.questions.length) * 100}%` }}
          />
        </div>
      </div>

      {/* QUESTIONS */}
      <div className="space-y-4">
        {data.questions.map((q: any, index: number) => {
          const isCorrect = q.your_answer === q.correct_answer;

          return (
            <div
              key={q.question_id}
              className={`bg-white p-5 rounded-2xl shadow border-l-4 ${
                isCorrect ? "border-green-500" : "border-red-500"
              }`}
            >
              <div className="flex justify-between items-start">
                <p className="font-medium">
                  Q{index + 1}. {q.question_text}
                </p>
                <span
                  className={`text-sm px-2 py-1 rounded ${
                    isCorrect ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                  }`}
                >
                  {isCorrect ? "Correct" : "Incorrect"}
                </span>
              </div>

              <div className="mt-4 space-y-2">
                {Object.entries(q.options).map(([key, text]: any) => {
                  const isUser = q.your_answer === key;
                  const isRight = q.correct_answer === key;

                  return (
                    <div
                      key={key}
                      className={`p-3 rounded-lg border ${
                        isRight
                          ? "bg-green-50 border-green-400"
                          : isUser
                          ? "bg-red-50 border-red-400"
                          : ""
                      }`}
                    >
                      {key}. {text}
                    </div>
                  );
                })}
              </div>

              <div className="mt-3 text-sm text-gray-600">
                <p>Your Answer: {q.your_answer || "Not answered"}</p>
                <p>Correct Answer: {q.correct_answer}</p>
                <p>Marks: {q.marks_obtained}</p>
              </div>

              <button
                onClick={() => handleExplain(q.question_id)}
                className="mt-3 text-blue-600 text-sm underline"
              >
                {loadingExplain === q.question_id
                  ? "Generating explanation..."
                  : "Explain with AI"}
              </button>

              {aiExplanations[q.question_id] && (
                <div className="mt-3 p-3 bg-blue-50 rounded text-sm leading-relaxed">
                  {aiExplanations[q.question_id]}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
