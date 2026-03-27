"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import StudyHeader from "@/features/study/components/StudyHeader";
import AIExplanationPanel from "@/features/study/components/AIExplanationPanel";
import AskAIChat from "@/features/ai/components/AskAIChat";
import WeekPlanner from "@/features/roadmap/components/WeekPlanner";
import { getTopicStudy } from "@/features/study/services/study.service";
import { createMockTest } from "@/features/mocktest/services/mocktest.services";
import YouTubeResources from "@/features/study/components/YoutubeResources";

export default function StudyPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();

  const topicId = Number(params.topicId ?? 0);
  const dayFromUrl = Number(searchParams.get("day"));

  const [selectedTopic, setSelectedTopic] = useState(topicId);
  const [selectedDay, setSelectedDay] = useState<number | null>(
    dayFromUrl || null
  );

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["topic-study", selectedTopic],
    queryFn: () => getTopicStudy(selectedTopic),
    staleTime: 1000 * 60 * 10,
    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  useEffect(() => {
    if (!isNaN(dayFromUrl)) {
      setSelectedDay(dayFromUrl);
    }
  }, [dayFromUrl]);

  const handleTopicChange = (newTopicId: number, day: number) => {
    setSelectedTopic(newTopicId);
    setSelectedDay(day);
    router.push(`/dashboard/study/${newTopicId}?day=${day}`);
  };

  const handleStartTest = async () => {
    if (!selectedDay || !data) {
      alert("Please select a day first");
      return;
    }

    try {
      const res = await createMockTest({
        topic_id: selectedTopic,
        roadmap_id: data.roadmap_id,
        day: selectedDay,
      });

      router.push(`/dashboard/mocktest/${res.mock_test.id}`);
    } catch (err) {
      console.error("Failed to start test", err);
    }
  };
console.log("DATA:",data);

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
      
      {/* ================= LEFT (PLANNER) ================= */}
      <div className="w-[350px] border-r bg-white overflow-y-auto">
        <WeekPlanner
          roadmapId={data.roadmap_id}
          week={data.week}
          studyMode
          selectedTopic={selectedTopic}
          onSelectTopic={handleTopicChange}
        />
      </div>

      {/* ================= RIGHT (CONTENT) ================= */}
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
        

  
        {/* ================= AI CHAT ================= */}
        <div className="mt-4">
          <AskAIChat context={data.topic} />
        </div>

         <div className="mt-3"> 
          <YouTubeResources
  topicName={data.topic}
  youtubeLinks={data.youtube_links || []}
/></div>


        {/* ================= CTA ================= */}
        <div className="mt-6">
          <button
            onClick={handleStartTest}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            Start Mock Test
          </button>
        </div>

      </div>
    </div>
  );
}

/* ================= HELPER ================= */

function extractYouTubeId(url: string) {
  const match = url.match(/v=([^&]+)/);
  return match ? match[1] : "";
}