'use client';

import { useEffect, useState } from 'react';

export function useCountdown(initialTime: number | undefined, onExpire: () => void) {
  const [timeLeft, setTimeLeft] = useState<number | null>(initialTime ?? null);

  useEffect(() => {
    if (timeLeft === null) return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null) return prev;

        if (prev <= 1) {
          clearInterval(interval);
          onExpire();
          return 0;
        }

        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft, onExpire]);

  return timeLeft;
}
