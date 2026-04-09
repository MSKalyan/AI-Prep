"use client";

import { useEffect, useState } from "react";

export function useQuestionIndex(testId: number) {
  const STORAGE_KEY = `mocktest_index_${testId}`;
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setCurrentIndex(Number(saved));
  }, [testId, STORAGE_KEY]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(currentIndex));
  }, [currentIndex, STORAGE_KEY]);

  return { currentIndex, setCurrentIndex };
}
