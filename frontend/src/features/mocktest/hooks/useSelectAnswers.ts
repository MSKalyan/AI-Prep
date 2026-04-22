'use client';

import { useEffect, useMemo, useState } from 'react';

interface Option {
  key: string;
  text: string;
}

interface Question {
  id: number;
  question_text: string;
  options: Option[];
}

interface MockTestData {
  attempt_id: number;
  remaining_seconds: number;
  questions: Question[];
}

export function useSelectedAnswers(data: MockTestData | undefined) {
  const restored = useMemo(() => {
    if (!data?.questions) return {};

    const result: Record<number, string> = {};
    return result;
  }, [data]);

  const [selected, setSelected] = useState<Record<number, string>>({});

  useEffect(() => {
    setSelected(restored);
  }, [restored]);

  return { selected, setSelected };
}
