"use client";

import { useQuery } from "@tanstack/react-query";
import { getExams } from "../services/roadmap.service";

export function useExams() {

  const query = useQuery({
    queryKey: ["exams"],
    queryFn: getExams,

    // optional optimizations
    staleTime: 1000 * 60 * 10, // cache for 10 minutes
  });

  return {
    exams: query.data,
    isLoading: query.isLoading,
    error: query.error,
  };
}