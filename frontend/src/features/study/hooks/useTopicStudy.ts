import { useQuery } from "@tanstack/react-query";
import { getTopicStudy } from "../services/study.service";

export function useTopicStudy(topicId: number) {
  return useQuery({
    queryKey: ["topic-study", topicId],
    queryFn: () => getTopicStudy(topicId),
    enabled: !!topicId,
    staleTime: 1000 * 60 * 10,
    retry: 1,
  });
}