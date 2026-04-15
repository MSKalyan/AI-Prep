'use client';

import { useEffect, useMemo, useState } from 'react';

interface Answer {
  question: number;
  user_answer: string;
}

interface MockTestData {
  answers?: Answer[];
}

export function useSelectedAnswers(data: MockTestData | undefined) {
  const restored = useMemo(() => {
    if (!data?.answers) return {};

    const result: Record<number, string> = {};
    data.answers.forEach((a: Answer) => {
      result[a.question] = a.user_answer;
    });
    return result;
  }, [data]);

  const [selected, setSelected] = useState<Record<number, string>>({});

  useEffect(() => {
    setSelected(restored);
  }, [restored]);

  return { selected, setSelected };
}
