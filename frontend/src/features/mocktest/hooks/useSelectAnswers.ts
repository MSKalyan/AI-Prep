"use client";

import { useEffect, useState } from "react";

export function useSelectedAnswers(data: any) {
  const [selected, setSelected] = useState<Record<number, string>>({});

  useEffect(() => {
    if (!data?.answers) return;

    const restored: Record<number, string> = {};
    data.answers.forEach((a: any) => {
      restored[a.question] = a.user_answer;
    });

    setSelected(restored);
  }, [data]);

  return { selected, setSelected };
}
