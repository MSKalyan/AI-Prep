"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getTopicStudy } from "@/features/study/services/study.service";
import { createMockTest } from "@/features/mocktest/services/mocktest.services";

export default function RevisionPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();

  const roadmapId = Number(searchParams.get("roadmapId"));
  const day = Number(searchParams.get("day"));
  const topicId = Number(params.topicId);

  const { data, isLoading } = useQuery({
    queryKey: ["revision-topic", topicId],
    queryFn: () => getTopicStudy(topicId),
  });

  const handleStartRevisionTest = async () => {
    try {
      const res = await createMockTest({
        roadmap_id: roadmapId,
        day: day,
      });

      router.push(`/dashboard/mocktest/${res.mock_test.id}`);
    } catch (err) {
      console.error("Revision test failed", err);
    }
  };

  if (isLoading || !data) {
    return <div className="px-4 sm:px-6 py-6">Loading...</div>;
  }

  return (
    <div className="px-4 sm:px-6 py-6 max-w-3xl mx-auto space-y-6">

      {/* TITLE */}
      <div>
        <h1 className="text-xl font-bold">{data.topic}</h1>
        <p className="text-sm text-gray-500">
          AI-generated explanation for quick revision
        </p>
      </div>

      {/* AI EXPLANATION */}
      <div className="border rounded p-4 bg-gray-50">
        <p className="text-sm text-gray-800 leading-relaxed">
          {data.ai_explanation || "No explanation available for this topic."}
        </p>
      </div>
{data.youtube_resources?.length > 0 && (
  <div className="space-y-3">
    <h2 className="text-sm font-semibold text-gray-700">
      Recommended Videos
    </h2>

  {data.youtube_resources.map((url: string, i: number) => (
        <a
          key={i}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="block border rounded p-3 bg-white hover:bg-gray-50 transition"
        >
          <p className="text-sm font-medium text-blue-600">
            ▶ Watch Video {i + 1}
          </p>
        </a>
      ))}
    </div>
)}
      {/* ACTION */}
      <div className="flex flex-col sm:flex-row gap-3">

        <button
          onClick={handleStartRevisionTest}
          className="w-full sm:w-auto bg-blue-600 text-white px-4 py-2 rounded"
        >
          Start Mock Test
        </button>

        <button
          onClick={() => router.back()}
          className="w-full sm:w-auto px-4 py-2 border rounded"
        >
          Back
        </button>

      </div>

    </div>
  );
}