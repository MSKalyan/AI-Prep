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

import {getTopicStudy} from "@/features/study/services/study.service";

interface Props {
  roadmapId: number;
  week: number;
  studyMode?: boolean;
  selectedTopic?: number;
  onSelectTopic?: (topicId: number) => void;
}

export default function WeekPlanner({
  roadmapId,
  week,
  studyMode = false,
  selectedTopic,
  onSelectTopic
}: Props) {

  const queryClient = useQueryClient();
  const router = useRouter();

  const [open, setOpen] = useState(studyMode);
  const [openTopic, setOpenTopic] = useState<number | null>(null);

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

    const topics: any[] | undefined = queryClient.getQueryData([
      "week-topics",
      roadmapId,
      week,
    ]);

    const topic = topics?.find((t) => t.id === id);
    const wasCompleted = topic?.completed;

    await toggleTopic(id);

    queryClient.setQueryData(
      ["week-topics", roadmapId, week],
      (old: any[]) =>
        old.map((t) =>
          t.id === id ? { ...t, completed: !t.completed } : t
        )
    );

    queryClient.setQueryData(
      ["roadmap-progress", roadmapId],
      (old: any) => {

        if (!old) return old;

        const change = wasCompleted ? -1 : +1;
        const completed = old.completed_topics + change;

        return {
          ...old,
          completed_topics: completed,
          progress: Math.round(
            (completed / old.total_topics) * 100
          ),
        };
      }
    );

    queryClient.setQueryData(
      ["week-progress", roadmapId, week],
      (old: any) => {

        if (!old) return old;

        const change = wasCompleted ? -1 : +1;
        const completed = old.completed_topics + change;

        return {
          ...old,
          completed_topics: completed,
          progress: Math.round(
            (completed / old.total_topics) * 100
          ),
        };
      }
    );
  }

  /* -------- Group by Day -------- */

  const grouped: Record<number, WeekTopic[]> = {};

  topics?.forEach((t) => {
    if (!grouped[t.day]) grouped[t.day] = [];
    grouped[t.day].push(t);
  });

  const days = Object.keys(grouped).map(Number).sort((a, b) => a - b);

  return (

    <div className="border rounded-lg bg-white">

      {/* Week Header */}

      <div
        className="flex justify-between items-center p-4 cursor-pointer"
        onClick={() =>  {  if (!studyMode) {
            setOpen(!open);}
          }}
      >

        <div className="font-semibold">
          Week {week}
        </div>

        <div className="flex items-center gap-4">

          {progress && (
            <div className="text-sm text-gray-500">
              {progress.progress}%
            </div>
          )}

          <span>
            {open ? "▲" : "▼"}
          </span>

        </div>

      </div>

      {/* Week Content */}

      {open && (

        <div className="p-4 space-y-4 border-t">

          {days.map((day) => {

            const dayTopics = grouped[day];

            const completed =
              dayTopics.filter((t) => t.completed).length;

            const progress =
              Math.round((completed / dayTopics.length) * 100);

            return (

              <div key={day} className="space-y-2">

                {/* Day Header */}

                <div className="flex justify-between text-sm font-medium">

                  <span>Day {day}</span>

                  <span className="text-gray-500">
                    {progress}%
                  </span>

                </div>

                {/* Day Progress */}

                <div className="h-2 bg-gray-200 rounded">

                  <div
                    className="h-2 bg-blue-500 rounded"
                    style={{ width: `${progress}%` }}
                  />

                </div>

                {/* Topics */}

                {dayTopics.map((t) => (

                  <div
                    key={t.id}
                    className={`flex items-center gap-3 border rounded p-2 cursor-pointer
                    ${selectedTopic === t.id ? "bg-blue-100 border-blue-400" : ""}
                    `}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (studyMode) {
                       queryClient.prefetchQuery({
      queryKey: ["topic-study", t.id],
      queryFn: () => getTopicStudy(t.id)
    });
                        onSelectTopic?.(t.id);
                      }
                    }}
                  >

                    <input
                      type="checkbox"
                      checked={t.completed}
                      onChange={(e) => {
                        e.stopPropagation();
                        handleToggle(t.id);
                      }}
                    />

                    <div className="flex-1">

                      <div>{t.topic}</div>

                      <div className="text-xs text-gray-500">
                        {t.hours} hrs
                      </div>

                    </div>

                    {/* Show Study button only in roadmap page */}

                    {!studyMode && (

                      <button
                        className="text-blue-600 text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/dashboard/study/${t.id}`);
                        }}
                      >
                        Study
                      </button>

                    )}

                  </div>

                ))}

              </div>

            );
          })}

        </div>

      )}

    </div>

  );
}