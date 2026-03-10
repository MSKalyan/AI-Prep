"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { getTopicExplanation } from "../services/study.service";
import { useState } from "react";

interface Props {
  topicId: number;
  explanation: string | null;
}

export default function AIExplanationPanel({ topicId, explanation }: Props) {
  console.log("AI explanation value:", explanation);

  const queryClient = useQueryClient();

  const [error, setError] = useState<string | null>(null);

  const generateExplanation = useMutation({
    mutationFn: () => getTopicExplanation(topicId),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["topic-study", topicId],
      });
    },

    onError: () => {
      setError("Failed to generate AI explanation.");
    }
  });

  // Explanation exists
  const hasExplanation =
  explanation &&
  explanation.trim() !== "" &&
  explanation !== "Explanation unavailable.";

if (hasExplanation){
    return (
      <div className="border rounded-lg p-4 bg-white space-y-3">

        <h2 className="font-semibold text-lg">
          AI Explanation
        </h2>

        <div className="text-base text-gray-700 whitespace-pre-wrap">
          {explanation}
        </div>

      </div>
    );
  }

  // Explanation missing
  return (
    <div className="border rounded-lg p-4 bg-gray-50 space-y-3">

      {error ? (
        <div className="text-red-600">
          {error}
        </div>
      ) : (
        <div className="text-gray-600">
          AI explanation has not been generated yet.
        </div>
      )}

      <button
        onClick={() => {
          setError(null);
          generateExplanation.mutate();
        }}
        disabled={generateExplanation.isPending}
        className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {generateExplanation.isPending
          ? "Generating explanation..."
          : error
          ? "Retry"
          : "Generate Explanation"}
      </button>

    </div>
  );
}