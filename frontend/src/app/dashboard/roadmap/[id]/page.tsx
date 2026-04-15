'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';

import { getRoadmapDetail } from '@/features/roadmap/services';
import { RoadmapPreview, WeekPlanner } from '@/features/roadmap/components';

export default function RoadmapDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const { data, isLoading, error } = useQuery({
    queryKey: ['roadmap', id],
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
    return <div className="px-4 sm:px-6 py-6 text-sm text-gray-600">Roadmap not found.</div>;
  }

  return (
    <div className="px-4 sm:px-6 py-6 max-w-5xl mx-auto space-y-6">
      <RoadmapPreview roadmap={data} />

      {Array.from({ length: data.total_weeks }, (_, i) => i + 1).map((week) => (
        <WeekPlanner key={week} roadmapId={id} week={week} />
      ))}
    </div>
  );
}
