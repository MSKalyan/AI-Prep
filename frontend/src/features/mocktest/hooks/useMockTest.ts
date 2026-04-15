'use client';

import { useQuery, useMutation } from '@tanstack/react-query';
import {
  createMockTest,
  getMockTestDetail,
  submitAnswer,
  getResults,
  generatePractice,
} from '../services/mocktest.service';

export function useCreateMockTest() {
  return useMutation({
    mutationFn: createMockTest,
  });
}

export function useMockTestDetail(id?: number) {
  return useQuery({
    queryKey: ['mocktest', id],
    queryFn: () => getMockTestDetail(id!),
    enabled: !!id,
  });
}

export function useSubmitAnswer() {
  return useMutation({
    mutationFn: submitAnswer,
  });
}

export function useResults() {
  return useQuery({
    queryKey: ['results'],
    queryFn: getResults,
  });
}

export function useGeneratePractice() {
  return useMutation({
    mutationFn: generatePractice,
  });
}
