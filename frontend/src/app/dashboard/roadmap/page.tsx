"use client";

import { useRouter } from "next/navigation";
import { useGenerateRoadmap } from "@/features/roadmap/hooks/useGenerateRoadmap";
import CreateRoadmapForm from "@/features/roadmap/components/CreateRoadmapForm";

export default function RoadmapPage() {
  const router = useRouter();
  const { generateRoadmap } = useGenerateRoadmap();

  const handleCreate = async (payload: any) => {
    const res = await generateRoadmap(payload);

    // Deterministic flow → direct redirect
    router.push(`/dashboard/roadmap/${res.roadmap_id}`);
  };

  return (
    <div className="px-4 sm:px-6 py-6">
      <CreateRoadmapForm />
    </div>
  );
}