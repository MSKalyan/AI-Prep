'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { generateRoadmap, deleteRoadmap } from '../services/roadmap.service';

export function useGenerateRoadmap() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: generateRoadmap,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps'] });
    },
    onError: (error) => {
      console.error('Roadmap generation failed:', error);
    },
  });

  return {
    generateRoadmap: mutation.mutateAsync,
    isLoading: mutation.isPending,
    error: mutation.error,
    data: mutation.data,
  };
}

export function useDeleteRoadmap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteRoadmap,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps'] });
    },
    onError: (error) => {
      console.error('Failed to delete roadmap:', error);
    },
  });
}
