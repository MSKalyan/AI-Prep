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
    return <div className="p-6">No roadmaps found</div>;
  }
  return (
    <div className="p-6 space-y-4">

      <h2 className="text-xl font-semibold">
        Your Roadmaps
      </h2>

      {data.map((roadmap: any) => (

        <div
          key={roadmap.id}
          className="flex items-center justify-between rounded-md border p-4 shadow-sm"
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
            className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            View
          </button>
          <button
            onClick={() => mutate(roadmap.id)}
            className="ml-2 rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700"
          >
            Delete
          </button>
        </div>

      ))}

    </div>
  );
}