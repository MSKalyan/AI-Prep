"use client";

import { useQuery } from "@tanstack/react-query";
import { getTopicExplanation } from "@/features/roadmap/services/roadmap.service";

export default function TopicExplanation({ topicId }: any) {

  const { data, isLoading } = useQuery({
    queryKey: ["topic-explanation", topicId],
    queryFn: () => getTopicExplanation(topicId),
  });

  if (isLoading) {
    return <div className="text-sm text-gray-500">Generating explanation...</div>;
  }

  return (
    <div className="text-sm text-gray-700 mt-2 bg-gray-50 p-3 rounded">
      {data?.explanation}
    </div>
  );
}