"use client";

import { useQuery } from "@tanstack/react-query";
import { getTopicStudy } from "../services/study.service";

interface Props {
  topicId: number;
}

export default function StudyHeader({ topicId }: Props) {

  const { data } = useQuery({
    queryKey: ["topic-study-header", topicId],
    queryFn: () => getTopicStudy(topicId)
  });

  if (!data) return null;

  return (
    <div className="border rounded-lg p-4 bg-white">

      <h1 className="text-xl font-semibold">
        {data.topic}
      </h1>

      <div className="text-sm text-gray-500 mt-1">

        Subject: {data.subject} • Week {data.week} • {data.phase}

      </div>

      <div className="text-sm mt-2">
        Study Time: <span className="font-medium">{data.estimated_hours} hrs</span>
      </div>

    </div>
  );
}