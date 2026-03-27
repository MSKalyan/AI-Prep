"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import {
  getWeekTopics,
  toggleTopic,
  getWeekProgress,
  WeekTopic
} from "@/features/roadmap/services/roadmap.service";

import { getTopicStudy } from "@/features/study/services/study.service";

interface Props {
  roadmapId: number;
  week: number;
  studyMode?: boolean;
  selectedTopic?: number;
  onSelectTopic?: (topicId: number, day:number) => void;
  onSelectDay?: (day: number) => void;
}

export default function WeekPlanner({
  roadmapId,
  week,
  studyMode = false,
  selectedTopic,
  onSelectTopic,
  onSelectDay
}: Props) {
  const queryClient = useQueryClient();
  const router = useRouter();

  const [open, setOpen] = useState(studyMode);

  const { data: topics } = useQuery({
    queryKey: ["week-topics", roadmapId, week],
    queryFn: () => getWeekTopics(roadmapId, week),
    enabled: open
  });

  const { data: progress } = useQuery({
    queryKey: ["week-progress", roadmapId, week],
    queryFn: () => getWeekProgress(roadmapId, week),
  });

  async function handleToggle(id: number) {
    const topicsList: any[] | undefined = queryClient.getQueryData(["week-topics", roadmapId, week]);
    const topic = topicsList?.find((t) => t.id === id);
    const wasCompleted = topic?.completed ?? topic?.is_completed;

    await toggleTopic(id);

    const updateProgress = (old: any) => {
      if (!old) return old;
      const change = wasCompleted ? -1 : +1;
      const completed = (old.completed_topics || 0) + change;
      return {
        ...old,
        completed_topics: completed,
        progress: Math.round((completed / old.total_topics) * 100),
      };
    };

    queryClient.setQueryData(["week-topics", roadmapId, week], (old: any[]) =>
      old.map((t) => (t.id === id ? { ...t, completed: !wasCompleted, is_completed: !wasCompleted } : t))
    );
    queryClient.setQueryData(["roadmap-progress", roadmapId], updateProgress);
    queryClient.setQueryData(["week-progress", roadmapId, week], updateProgress);
  }

  const grouped: Record<number, WeekTopic[]> = {};
  topics?.forEach((t: any) => {
    const d = t.day || t.day_number || 1;
    if (!grouped[d]) grouped[d] = [];
    grouped[d].push(t);
  });

  const days = Object.keys(grouped).map(Number).sort((a, b) => a - b);

  return (
    <div className="border rounded-xl bg-white shadow-sm overflow-hidden mb-4">
      <div
        className={`flex justify-between items-center p-5 cursor-pointer transition-colors ${open ? 'bg-gray-50' : 'hover:bg-gray-50'}`}
        onClick={() => { if (!studyMode) setOpen(!open); }}
      >
        <div>
          <h3 className="text-lg font-bold text-gray-800">Week {week}</h3>
          <p className="text-xs text-gray-500 italic">Maximize coverage and test performance</p>
        </div>

        <div className="flex items-center gap-4">
          {progress && (
            <div className="flex flex-col items-end">
              <span className="text-sm font-semibold text-blue-600">{progress.progress}%</span>
              <div className="w-24 h-1.5 bg-gray-200 rounded-full mt-1">
                <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${progress.progress}%` }} />
              </div>
            </div>
          )}
          <span className="text-gray-400">{open ? "▲" : "▼"}</span>
        </div>
      </div>

      {open && (
        <div className="p-4 space-y-6 border-t bg-gray-50/30">
          {days.map((day) => {
            const dayTopics = grouped[day];
            const completedCount = dayTopics.filter((t: any) => t.completed || t.is_completed).length;
            const dayProgress = Math.round((completedCount / dayTopics.length) * 100);

            return (
              <div key={day} className="space-y-3" >
                <div className="flex items-center gap-2">
                   <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                     day === 7 ? "bg-red-100 text-red-700" : 
                     day === 6 ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-600"
                   }`}>
                     Day {day} {day === 7 ? "• Mock Test" : day === 6 ? "• Revision" : ""}
                   </span>
                   <div className="flex-1 h-px bg-gray-200"></div>
                   <span className="text-[10px] font-medium text-gray-400">{dayProgress}% Done</span>
                </div>

                <div className="grid grid-cols-1 gap-2">
                  {dayTopics.map((t: any) => {
                    // Logic to handle Phase colors and labels
                    const currentPhase = t.phase?.toLowerCase();
                    const isRevision = currentPhase === "revision" || day === 6;
                    const isMock = currentPhase === "practice" || currentPhase === "test" || day === 7;
                    
                    const statusColor = isMock ? "border-l-red-500" : isRevision ? "border-l-amber-500" : "border-l-blue-500";
                    const buttonLabel = isMock ? "Take Test" : isRevision ? "Revise" : "Study";
                    const buttonStyle = isMock ? "bg-red-50 text-red-600 hover:bg-red-100" : isRevision ? "bg-amber-50 text-amber-600 hover:bg-amber-100" : "bg-blue-50 text-blue-600 hover:bg-blue-100";
                    console.log(t);
                    return (
                      <div
                        key={t.id}
                        onClick={() => {  if (studyMode) {
    queryClient.prefetchQuery({
      queryKey: ["topic-study", t.id],
      queryFn: () => getTopicStudy(t.id)
    });

    onSelectTopic?.(t.id,day);
    router.push(`/dashboard/study/${t.id}?day=${day}`);  // 🔥 SET TOPIC
  }
                        }}
                        className={`flex items-center gap-4 border-2 rounded-lg p-3 transition-all cursor-pointer
                          ${selectedTopic === t.id ? "border-blue-500 bg-blue-50 ring-2 ring-blue-100" : "bg-white border-transparent shadow-sm hover:border-gray-200"}
                          border-l-4 ${statusColor}
                        `}
                      >
                        <input
                          type="checkbox"
                          className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                          checked={!!(t.completed || t.is_completed) || false}
                          onChange={(e) => { e.stopPropagation(); handleToggle(t.id); }}
                        />

                        <div className="flex-1">
                          <div className="font-semibold text-gray-800 text-sm leading-tight">{t.topic || t.topic_name}</div>
                          <div className="flex gap-2 mt-1">
                            <span className="text-[10px] font-medium text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">{t.subject || t.subject_name}</span>
                            <span className="text-[10px] font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">{t.hours || t.estimated_hours} hrs</span>
                          </div>
                        </div>

                        {!studyMode && (
                          <button
                            className={`px-3 py-1 rounded text-xs font-bold transition-colors ${buttonStyle}`}
                            onClick={(e) => { e.stopPropagation(); router.push(`/dashboard/study/${t.id}`); }}
                          >
                            {buttonLabel}
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}