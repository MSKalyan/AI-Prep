"use client";

import { useRouter } from "next/navigation";
import { useRoadmaps } from "@/features/roadmap/hooks/useRoadmapJob";
import { useDeleteRoadmap } from "@/features/roadmap/hooks/useGenerateRoadmap";

export default function RoadmapsPage() {

  const router = useRouter();
const { mutate } = useDeleteRoadmap();

  const { data, isLoading, error } = useRoadmaps();

  if (isLoading) {
    return <div className="p-6">Loading roadmaps...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-500">Failed to load roadmaps</div>;
  }

  if (!data || data.length === 0) {
    return <div className="px-4 sm:px-6 py-6">No roadmaps found</div>;
  }
  return (
    <div className="px-4 sm:px-6 py-6 max-w-4xl mx-auto space-y-6">

      <h2 className="text-2xl sm:text-3xl font-semibold">
        Your Roadmaps
      </h2>

      {data.map((roadmap: any) => (

        <div
          key={roadmap.id}
          className="grid gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-center rounded-md border bg-white p-4 sm:p-5 shadow-sm"
        >

          <div>
            <p className="font-medium">
              {roadmap.exam?.name}
            </p>
            <p className="text-sm text-gray-500">
              Target Date: {roadmap.target_date}
            </p>
          </div>

          <button
            onClick={() =>
              router.push(`/dashboard/roadmap/${roadmap.id}`)
            }
            className="rounded-md bg-black px-4 py-2 text-white hover:bg-black/80"
          >
            View
          </button>
          <button
            onClick={() => mutate(roadmap.id)}
            className="rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700"
          >
            Delete
          </button>
        </div>

      ))}

    </div>
  );
}