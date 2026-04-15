'use client';

import { useQuery } from '@tanstack/react-query';
import { getExams } from '../services/roadmap.service';

export function useExams() {
  return useQuery({
    queryKey: ['exams'],
    queryFn: getExams,
  });
}
