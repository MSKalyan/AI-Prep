'use client';

import Image from 'next/image';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getTopicStudy } from '@/features/study/services';
import { createMockTest } from '@/features/mocktest/services';

export default function RevisionPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();

  const roadmapId = Number(searchParams.get('roadmapId'));
  const day = Number(searchParams.get('day'));
  const topicId = Number(params.topicId);

  const { data, isLoading } = useQuery({
    queryKey: ['revision-topic', topicId],
    queryFn: () => getTopicStudy(topicId),
  });

  const handleStartRevisionTest = async () => {
    try {
      const res = await createMockTest({
        roadmap_id: roadmapId,
        day,
        topic_id: topicId,
      });

      router.push(`/dashboard/mocktest/${res.mock_test.id}`);
    } catch {
    }
  };

  if (isLoading || !data) {
    return <div className="px-4 sm:px-6 py-6">Loading...</div>;
  }

  const explanationBlocks = splitExplanation(data.ai_explanation || '');
  const videoLinks: string[] = (data.youtube_links || data.youtube_resources || []).slice(0, 6);

  return (
    <div className="px-4 sm:px-6 py-6 max-w-5xl mx-auto space-y-6">
      <div className="rounded-2xl border bg-gradient-to-br from-blue-50 to-white p-5 sm:p-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{data.topic}</h1>
        <p className="text-sm text-gray-600 mt-1">
          Focused revision notes with curated videos and a topic-specific test.
        </p>
      </div>

      <div className="border rounded-xl p-4 sm:p-5 bg-white">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Revision Notes</h2>
        {explanationBlocks.length > 0 ? (
          <div className="space-y-3 text-sm text-gray-800 leading-7">
            {explanationBlocks.map((block) => (
              <p key={block}>{block}</p>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-600">No explanation available for this topic.</p>
        )}
      </div>

      {videoLinks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">Recommended Videos</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {videoLinks.map((url: string) => {
              const videoId = extractYouTubeId(url);
              if (!videoId) return null;

              return (
                <a
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block border rounded-xl overflow-hidden bg-white hover:shadow-md transition"
                >
                  <Image
                    src={`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`}
                    alt={`${data.topic} video thumbnail`}
                    width={480}
                    height={270}
                    className="w-full h-40 object-cover"
                  />
                  <div className="p-3">
                    <p className="text-sm font-semibold text-gray-900 line-clamp-2">Revise {data.topic}</p>
                    <p className="text-xs text-blue-600 mt-1">Watch on YouTube</p>
                  </div>
                </a>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={handleStartRevisionTest}
          className="w-full sm:w-auto bg-blue-600 text-white px-4 py-2 rounded-lg"
        >
          Start Mock Test
        </button>

        <button onClick={() => router.back()} className="w-full sm:w-auto px-4 py-2 border rounded-lg">
          Back
        </button>
      </div>
    </div>
  );
}

function splitExplanation(text: string): string[] {
  return text
    .split(/\n{2,}/g)
    .map((item) => item.replace(/^\s*[-*]\s*/gm, '').trim())
    .filter(Boolean);
}

function extractYouTubeId(url: string): string {
  const patterns = [/v=([^&]+)/, /youtu\.be\/([^?&]+)/, /\/shorts\/([^?&]+)/];
  for (const pattern of patterns) {
    const match = pattern.exec(url);
    if (match?.[1]) return match[1];
  }
  return '';
}
