'use client';

import { useEffect, useState } from 'react';

export function useQuestionIndex(testId: number) {
  const STORAGE_KEY = `mocktest_index_${testId}`;
  const [currentIndex, setCurrentIndex] = useState(() => {
    if (globalThis.window !== undefined) {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? Number(saved) : 0;
    }
    return 0;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(currentIndex));
  }, [currentIndex, STORAGE_KEY]);

  return { currentIndex, setCurrentIndex };
}
