'use client';

import { useEffect } from 'react';
import { apiClient } from '@/lib/apiClient';

export function useMockTestController(testId: number) {
  useEffect(() => {
    if (!testId) return;

    const startTest = async () => {
      try {
        await apiClient.post(`/mocktest/start/${testId}/`);
      } catch {
      }
    };

    startTest();
  }, [testId]);
}
