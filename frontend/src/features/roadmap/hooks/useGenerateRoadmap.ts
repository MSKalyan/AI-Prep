import { useMutation } from "@tanstack/react-query";
import { generateRoadmap } from "../services/roadmap.service";

export function useGenerateRoadmap(){

  const mutation = useMutation({
    mutationFn: generateRoadmap,
  });

  return {
    createRoadmap: mutation.mutateAsync,
    isGenerating: mutation.isPending
  };
}
