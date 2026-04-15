'use client';

import { useParams } from 'next/navigation';

export function useAttemptId() {
  const params = useParams();

  const rawId = params?.id;

  let attemptId: number | null = null;
  if (typeof rawId === 'string') {
    attemptId = Number(rawId);
  } else if (Array.isArray(rawId)) {
    attemptId = Number(rawId[0]);
  }

  return attemptId;
}
