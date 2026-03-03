import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as roadmap from "../services/roadmap.service";

export function useGenerateRoadmap() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: roadmap.generateRoadmap,

    onSuccess: (data) => {
      // Invalidate roadmap list so new roadmap appears
      queryClient.invalidateQueries({ queryKey: ["roadmaps"] });
    },

    onError: (error) => {
      console.error("Roadmap generation failed:", error);
    },
  });

  return {
    generateRoadmap: mutation.mutateAsync,
    isLoading: mutation.isPending,
    error: mutation.error,
    data: mutation.data, // useful if needed
  };
}

export function useDeleteRoadmap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: roadmap.deleteRoadmap,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roadmaps"] });
    },
    onError: (error) => {
      console.error("Failed to delete roadmap:", error);
    },
  });
}