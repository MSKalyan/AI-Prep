"use client";

import { useQuery } from "@tanstack/react-query";
import { getRoadmapProgress } from "../services/roadmap.service";

interface Roadmap {
  id: number;
  exam?: {
    id: number;
    name: string;
  };
  target_date: string;
  difficulty_level: string;
  total_weeks: number;
  description?: string;
}

interface Props {
  roadmap: Roadmap;
}

export default function RoadmapPreview({ roadmap }: Props) {
const { data: progress } = useQuery({
  queryKey: ["roadmap-progress", roadmap.id],
  queryFn: () => getRoadmapProgress(roadmap.id),
});
  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">

      <h2 className="text-2xl font-semibold text-gray-800">
        {roadmap.exam?.name ?? "Study Roadmap"}
      </h2>

      <div className="mt-2 text-sm text-gray-600 space-y-1">
        <p>
          <strong>Target Date:</strong> {roadmap.target_date}
        </p>

        <p>
          <strong>Total Weeks:</strong> {roadmap.total_weeks}
        </p>

        <p>
          <strong>Difficulty:</strong> {roadmap.difficulty_level}
        </p>
      </div>

      {roadmap.description && (
        <p className="mt-4 text-sm text-gray-700">
          {roadmap.description}
        </p>
      )}
      {progress && (
  <div className="mt-4 space-y-1">

    <div className="flex justify-between text-sm text-gray-600">
      <span>Overall Progress</span>
      <span>{progress.progress}%</span>
    </div>

    <div className="h-2 bg-gray-200 rounded">

      <div
        className="h-2 bg-green-500 rounded"
        style={{ width: `${progress.progress}%` }}
      />

    </div>

    <div className="text-xs text-gray-500">
      {progress.completed_topics} / {progress.total_topics} topics completed
    </div>

  </div>
)}

    </div>
  );
}