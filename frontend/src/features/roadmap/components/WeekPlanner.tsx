"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import {
  getWeekTopics,
  toggleTopic,
  getWeekProgress,
  WeekTopic,
  WeekPlanResponse
} from "@/features/roadmap/services/roadmap.service";

import { getTopicStudy } from "@/features/study/services/study.service";

interface Props {
  roadmapId: number;
  week: number;
  studyMode?: boolean;
  selectedTopic?: number;
  onSelectTopic?: (topicId: number, day: number) => void;
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

  const { data: response } = useQuery<WeekPlanResponse>({
    queryKey: ["week-topics", roadmapId, week],
    queryFn: () => getWeekTopics(roadmapId, week),
    enabled: open
  });

  const topics = response?.data || [];
  const revision = response?.today_revision || [];

  console.log("revison data:",revision);
  const { data: progress } = useQuery({
    queryKey: ["week-progress", roadmapId, week],
    queryFn: () => getWeekProgress(roadmapId, week),
  });

  const grouped: Record<number, WeekTopic[]> = {};
  topics.forEach((t: any) => {
    const d = t.day || t.day_number || 1;
    if (!grouped[d]) grouped[d] = [];
    grouped[d].push(t);
  });

  const days = Object.keys(grouped).map(Number).sort((a, b) => a - b);

  const currentDay = (() => {
    for (const day of days) {
      const dayItems = grouped[day];
      const allCompleted = dayItems.every(
        (t: any) => t.completed || t.is_completed
      );

      if (!allCompleted) return day;
    }

    return days[days.length - 1];
  })();

  async function handleToggle(id: number) {
  const response: any = queryClient.getQueryData([
    "week-topics",
    roadmapId,
    week
  ]);

  const topicsList = response?.data || [];

  const topic = topicsList.find((t: any) => t.id === id);
  const wasCompleted = topic?.completed ?? topic?.is_completed;

  await toggleTopic(id);

  queryClient.setQueryData(
    ["week-topics", roadmapId, week],
    (old: any) => {
      if (!old) return old;

      return {
        ...old,
        data: old.data.map((t: any) =>
          t.id === id
            ? { ...t, completed: !wasCompleted, is_completed: !wasCompleted }
            : t
        )
      };
    }
  );
}
  return (
    <div className="border rounded-xl bg-white shadow-sm overflow-hidden mb-4">

      <div
        className={`flex justify-between items-center p-5 cursor-pointer ${open ? 'bg-gray-50' : 'hover:bg-gray-50'}`}
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
                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${progress.progress}%` }} />
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
              <div key={day} className="space-y-3">

                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                    Day {day}
                  </span>

                  {day === currentDay && (
                    <span className="text-[10px] text-blue-600 font-medium">
                      Today
                    </span>
                  )}

                  <div className="flex-1 h-px bg-gray-200"></div>

                  <span className="text-[10px] text-gray-400">
                    {dayProgress}% Done
                  </span>
                </div>

                {day === currentDay && revision.length > 0 && (
                  <div
                    className="p-3 bg-red-50 border border-red-200 rounded-lg cursor-pointer hover:bg-red-100 transition"
                    onClick={() => {
  if (revision.length > 0) {
    const randomIndex = Math.floor(Math.random() * revision.length);
    const selected = revision[randomIndex];

    console.log("REVISION SELECTED:", selected);

    router.push(
      `/dashboard/study/${selected.topic_id}?mode=revision&day=${day}`
    );
  }
}}
                  >
                    <p className="text-xs font-semibold text-red-600 mb-1">
                      🔁 Revise (based on previous performance)
                    </p>

                    <ul className="list-disc ml-4 text-xs text-gray-700">
                      {revision.map((r: any) => (
                        <li key={r.topic_id}>{r.topic_name}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="grid gap-2">
                  {dayTopics.map((t: any) => {

                    const phase = t.phase?.toLowerCase();
                    const isMock = phase === "practice" || day === 7;

                    const buttonLabel = isMock ? "Take Test" : "Study";

                    return (
                      <div
                        key={t.id}
                        onClick={() => {
                          if (studyMode) {
                            queryClient.prefetchQuery({
                              queryKey: ["topic-study", t.id],
                              queryFn: () => getTopicStudy(t.id)
                            });

                            onSelectTopic?.(t.id, day);
                            router.push(`/dashboard/study/${t.id}?day=${day}`);
                          }
                        }}
className={`flex items-center gap-4 border rounded-lg p-3 cursor-pointer transition
  ${t.completed || t.is_completed
    ? "bg-green-50 border-green-300"
    : "bg-white hover:border-gray-300 hover:bg-gray-50"}
`}                      >
                        <input
                        className="w-4 h-4 accent-green-600"
                          type="checkbox"
                          checked={!!(t.completed || t.is_completed)}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleToggle(t.id);
                          }}
                        />

                        <div className="flex-1">
                          <div className="font-semibold text-sm">
                            {t.topic}
                          </div>

                          <div className="flex gap-2 mt-1">
                            <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                              {t.subject}
                            </span>

                            <span className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                              {t.hours} hrs
                            </span>
                          </div>
                        </div>

                        {!studyMode && (
                          <button
                            className="px-3 py-1 text-xs font-bold bg-blue-50 text-blue-600 rounded"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/dashboard/study/${t.id}`);
                            }}
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