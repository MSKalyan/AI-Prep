"use client";

import { useQuery } from "@tanstack/react-query";
import { getTopicStudy } from "../services/study.service";

interface Props {
  topicId: number;
}

export default function AIExplanationPanel({ topicId }: Props) {

  const { data, isLoading } = useQuery({
    queryKey: ["topic-study", topicId],
    queryFn: () => getTopicStudy(topicId),
  });

  if (isLoading) {
    return (
      <div className="border rounded-lg p-4 bg-white">
        Loading explanation...
      </div>
    );
  }

  return (

    <div className="border rounded-lg p-4 bg-white space-y-3">

      <h2 className="font-semibold text-lg">
        AI Explanation
      </h2>

      <div className="text-base text-gray-700 leading-relaxed whitespace-pre-wrap">
        {data?.ai_explanation || "No explanation available."}
      </div>

    </div>

  );
}