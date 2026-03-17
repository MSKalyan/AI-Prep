"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery ,keepPreviousData} from "@tanstack/react-query";
import { useState } from "react";

import StudyHeader from "@/features/study/components/StudyHeader";
import AIExplanationPanel from "@/features/study/components/AIExplanationPanel";
import AskAIChat from "@/features/ai/components/AskAIChat";
import WeekPlanner from "@/features/roadmap/components/WeekPlanner";
import { getTopicStudy } from "@/features/study/services/study.service";

export default function StudyPage() {

  const params = useParams();
  const router = useRouter();

  const topicId = Number(params.topicId ?? 0);
  const [selectedTopic, setSelectedTopic] = useState(topicId);

  const {
    data,
    isLoading,
    isError,
    refetch,
    isFetching
  } = useQuery({
    queryKey: ["topic-study", selectedTopic],
    queryFn: () => getTopicStudy(selectedTopic),

    staleTime: 1000 * 60 * 10,

    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  if (isLoading) {
    return (
      <div className="p-6 animate-pulse space-y-3">
        <div className="h-6 w-48 bg-gray-200 rounded"></div>
        <div className="h-4 w-full bg-gray-200 rounded"></div>
        <div className="h-4 w-5/6 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-6 space-y-4">

        <div className="text-red-600 font-medium">
          Failed to load topic data.
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {isFetching ? "Retrying..." : "Retry"}
        </button>

      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-80px)]">

      <div className="w-[350px] border-r bg-white overflow-y-auto">

        <WeekPlanner
          roadmapId={data.roadmap_id}
          week={data.week}
          studyMode
          selectedTopic={selectedTopic}
          onSelectTopic={setSelectedTopic}
        />

      </div>

      <div className="flex-1 p-6 space-y-6 overflow-y-auto">

        <button
          onClick={() =>
            router.push(`/dashboard/roadmap/${data.roadmap_id}`)
          }
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to Roadmap
        </button>

        <StudyHeader topicId={selectedTopic} />

        <AIExplanationPanel
          topicId={selectedTopic}
          explanation={data.ai_explanation}
        />

        <div className="mt-3">
          <AskAIChat context={data.topic} />
        </div>

      </div>

    </div>
  );
}