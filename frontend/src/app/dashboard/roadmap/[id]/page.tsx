"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { getRoadmapDetail } from "@/features/roadmap/services/roadmap.service";
import RoadmapPreview from "@/features/roadmap/components/RoadmapPreview";

export default function RoadmapDetailPage() {

  const params = useParams();
  const id = Number(params.id);

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
    return (
      <div className="p-6 text-sm text-gray-600">
        Loading roadmap...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-sm text-red-500">
        Failed to load roadmap.
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 text-sm text-gray-600">
        Roadmap not found.
      </div>
    );
  }

  return (
    <div className="p-6">
      <RoadmapPreview roadmap={data} />
    </div>
  );
}