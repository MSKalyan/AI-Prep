'use client';

import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { StudyHeader, AIExplanationPanel, YouTubeResources } from '@/features/study/components';
import { AskAIChat } from '@/features/ai/components';
import { WeekPlanner } from '@/features/roadmap/components';
import { getTopicStudy } from '@/features/study/services';
import { createMockTest } from '@/features/mocktest/services';

export default function StudyPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();

  const mode = searchParams.get('mode'); // ✅ revision mode
  const topicId = Number(params.topicId ?? 0);
  const dayFromUrl = Number(searchParams.get('day'));
  const [isStartingTest, setIsStartingTest] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState(topicId);
  const [selectedDay, setSelectedDay] = useState<number | null>(dayFromUrl || null);

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['topic-study', selectedTopic],
    queryFn: () => getTopicStudy(selectedTopic),
    staleTime: 1000 * 60 * 10,
    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  useEffect(() => {
    if (!Number.isNaN(dayFromUrl)) {
      setSelectedDay(dayFromUrl);
    }
  }, [dayFromUrl]);

  // ✅ Preserve revision mode when switching topics
  const handleTopicChange = (newTopicId: number, day: number) => {
    setSelectedTopic(newTopicId);
    setSelectedDay(day);

    const url =
      mode === 'revision'
        ? `/dashboard/study/${newTopicId}?day=${day}&mode=revision`
        : `/dashboard/study/${newTopicId}?day=${day}`;

    router.push(url);
  };

  const handleStartTest = async () => {
    if (!selectedDay || !data) {
      alert('Please select a day first');
      return;
    }

    setIsStartingTest(true);

    try {
      const res = await createMockTest({
        topic_id: selectedTopic,
        roadmap_id: data.roadmap_id,
        day: selectedDay,
      });

      router.push(`/dashboard/mocktest/${res.mock_test.id}`);
    } catch (err) {
      console.error('Failed to start test', err);
    } finally {
      setIsStartingTest(false);
    }
  };
  if (data?.error) {
    return <div className="p-4 sm:p-6 text-red-600">Invalid revision topic. Please try again.</div>;
  }
  if (isLoading) {
    return (
      <div className="p-4 sm:p-6 animate-pulse space-y-3">
        <div className="h-6 w-48 bg-gray-200 rounded"></div>
        <div className="h-4 w-full bg-gray-200 rounded"></div>
        <div className="h-4 w-5/6 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-4 sm:p-6 space-y-4">
        <div className="text-red-600 font-medium">Failed to load topic data.</div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {isFetching ? 'Retrying...' : 'Retry'}
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row lg:min-h-[calc(100vh-80px)]">
      {/* ================= LEFT (PLANNER) ================= */}
      <div className="hidden lg:flex lg:w-80 border-r border-b lg:border-b-0 bg-white overflow-y-auto">
        <WeekPlanner
          roadmapId={data.roadmap_id}
          week={data.week}
          studyMode
          onSelectTopic={handleTopicChange}
        />
      </div>

      {/* ================= RIGHT (CONTENT) ================= */}
      <div className="flex-1 p-4 sm:p-6 space-y-6 overflow-y-auto">
        {/* BACK */}
        <button
          onClick={() => router.push(`/dashboard/roadmap/${data.roadmap_id}`)}
          className="text-xs sm:text-sm text-blue-600 hover:underline"
        >
          ← Back to Roadmap
        </button>

        {/* ✅ REVISION MODE BANNER */}
        {mode === 'revision' && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded text-xs sm:text-sm text-yellow-700">
            🔁 Revision Mode — Focus on weak areas and recall actively
          </div>
        )}

        <StudyHeader topicId={selectedTopic} />

        <AIExplanationPanel topicId={selectedTopic} explanation={data.ai_explanation} />

        {/* AI CHAT */}
        <div className="mt-4">
          <AskAIChat context={data.topic} />
        </div>

        {/* YOUTUBE */}
        <div className="mt-3">
          <YouTubeResources topicName={data.topic} youtubeLinks={data.youtube_links || []} />
        </div>

        {/* CTA */}
        <div className="mt-6 flex flex-col sm:flex-row gap-3">
          {/* Mock Test */}
          <button
            onClick={handleStartTest}
            disabled={isStartingTest}
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm sm:text-base"
          >
            {isStartingTest ? 'Generating Mock Test...' : 'Start Mock Test'}
          </button>

          {/* ✅ Optional: Mark Revised */}
          {mode === 'revision' && (
            <button className="bg-green-100 text-green-700 px-4 py-2 rounded text-sm sm:text-base">
              Mark as Revised
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
