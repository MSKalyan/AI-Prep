"use client";

import { useState } from "react";
import { explainQuestion } from "../services/mocktest.service";

export function useAIExplanation() {
  const [aiExplanations, setAiExplanations] = useState<Record<number, string>>({});
  const [loadingExplain, setLoadingExplain] = useState<number | null>(null);

  const handleExplain = async (questionId: number) => {
    try {
      setLoadingExplain(questionId);

      const res = await explainQuestion(questionId);

      setAiExplanations((prev) => ({
        ...prev,
        [questionId]: res.explanation,
      }));
    } catch {
      alert("Failed to generate explanation");
    } finally {
      setLoadingExplain(null);
    }
  };

  return {
    aiExplanations,
    loadingExplain,
    handleExplain,
  };
}
