"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getRoadmapTopics } from "../services/study.service";
import {useEffect, useRef} from "react";

interface SidebarTopic {
  id: number;
  topic: string;
  week: number;
  completed: boolean;
}

interface Props {
  topicId: number;
  roadmapId: number;
}

export default function StudySidebar({ topicId, roadmapId }: Props) {

  const router = useRouter();
  const activeRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
  activeRef.current?.scrollIntoView({
    behavior: "smooth",
    block: "center",
  });
}, []);
  const { data: topics, isLoading } = useQuery({
    queryKey: ["roadmap-topics", roadmapId],
    queryFn: () => getRoadmapTopics(roadmapId),
  });

  if (isLoading || !topics) {
    return (
      <div className="p-4 text-sm text-gray-500">
        Loading topics...
      </div>
    );
  }

  /* ---------- Group topics by week ---------- */

  const grouped: Record<number, SidebarTopic[]> = {};

  topics.forEach((t: SidebarTopic) => {
    if (!grouped[t.week]) grouped[t.week] = [];
    grouped[t.week].push(t);
  });

  const weeks = Object.keys(grouped)
    .map(Number)
    .sort((a, b) => a - b);

  const activeWeek = topics.find((t: SidebarTopic) => t.id === topicId)?.week;
  return (

    <div className="p-4">

      <h2 className="font-semibold mb-4">
        Roadmap
      </h2>

      <div className="space-y-4">

        {weeks.map((week) => (

          <div key={week}>

            {/* Week header */}

           <div
  className={`text-xs font-semibold mb-2
  ${week === activeWeek ? "text-blue-600" : "text-gray-500"}
`}
>
  Week {week}
</div>

            {/* Topics */}

            <div className="space-y-1">

              {grouped[week].map((t) => (

                <div
                  key={t.id}
                  ref={t.id === topicId ? activeRef : null}
                  onClick={() => router.push(`/dashboard/study/${t.id}`)}
                  className={`flex items-center justify-between p-2 rounded cursor-pointer text-sm transition
                  ${
                    t.id === topicId
                      ? "bg-blue-100 text-blue-700 font-medium"
                      : "hover:bg-gray-100"
                  }`}
                >

                <span>{t.topic}</span>

                {t.completed && (
                  <span className="text-green-600 text-xs">✓</span>
                )}
                </div>

              ))}

            </div>

          </div>

        ))}

      </div>

    </div>
  );
}