"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { getRoadmapDetail } from "@/features/roadmap/services/roadmap.service";
import RoadmapPreview from "@/features/roadmap/components/RoadmapPreview";
import WeekPlanner from "@/features/roadmap/components/WeekPlanner";

export default function RoadmapDetailPage() {

  const params = useParams();
  const id = Number(params.id);

  const [week, setWeek] = useState(1);

  const {
    data,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["roadmap", id],
    queryFn: () => getRoadmapDetail(id),
    enabled: Number.isFinite(id),
  });

  if (isLoading) {
    return <div className="p-6 text-sm text-gray-600">Loading roadmap...</div>;
  }

  if (error) {
    return <div className="p-6 text-sm text-red-500">Failed to load roadmap.</div>;
  }

  if (!data) {
    return <div className="p-6 text-sm text-gray-600">Roadmap not found.</div>;
  }

  const weeks = Array.from({ length: data.total_weeks }, (_, i) => i + 1);

  return (
    <div className="p-6 space-y-6">

      <RoadmapPreview roadmap={data} />

    {Array.from({ length: data.total_weeks }, (_, i) => i + 1).map((week) => (
  <WeekPlanner
    key={week}
    roadmapId={id}
    week={week}
  />
))}

      {/* Week planner */}
      <WeekPlanner roadmapId={id} week={week} />

    </div>
  );
}