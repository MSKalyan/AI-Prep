"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import StudySidebar from "@/features/study/components/StudySidebar";
import StudyHeader from "@/features/study/components/StudyHeader";
import AIExplanationPanel from "@/features/study/components/AIExplanationPanel";
import {useState} from "react";
import { getTopicStudy } from "@/features/study/services/study.service";

import WeekPlanner from "@/features/roadmap/components/WeekPlanner";

export default function StudyPage() {

  const params = useParams();
  const topicId = Number(params.topicId);
  const [selectedTopic, setSelectedTopic] = useState(topicId);
  const router = useRouter();
 
 
  const { data, isLoading } = useQuery({
 queryKey: ["topic-study", selectedTopic],
  queryFn: () => getTopicStudy(selectedTopic),

  staleTime: 1000 * 60 * 10,
  refetchOnMount: false,
  refetchOnWindowFocus: false,
  refetchOnReconnect: false,
  placeholderData: (previousData) => previousData
});

  if (isLoading || !data) {
    return <div className="p-6">Loading...</div>;
  }

  return (

    <div className="flex h-[calc(100vh-80px)]">

      {/* <div className="w-[300px] border-r bg-white overflow-y-auto">

        <StudySidebar
          topicId={topicId}
          roadmapId={data.roadmap_id}
        />

      </div> */}
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

        <AIExplanationPanel topicId={selectedTopic} />

      </div>

    </div>
  );
}