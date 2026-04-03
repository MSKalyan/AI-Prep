"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createMockTest } from "@/features/mocktest/services/mocktest.services";
export const dynamic = "force-dynamic";
export default function MockTestPage() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const init = async () => {
      try {
        // ✅ Get raw params (DO NOT convert immediately)
        const topicIdRaw = params.get("topicId");
        const roadmapIdRaw = params.get("roadmapId");
        const dayRaw = params.get("day");

        // ✅ Validate params
        if (!topicIdRaw || !roadmapIdRaw || !dayRaw) {
          console.error("Missing required params:", {
            topicIdRaw,
            roadmapIdRaw,
            dayRaw,
          });

          alert("Invalid test request. Please select a topic and day.");
          router.replace("/dashboard/roadmap");
          return;
        }

        // ✅ Convert AFTER validation
        const topicId = Number(topicIdRaw);
        const roadmapId = Number(roadmapIdRaw);
        const day = Number(dayRaw);

        // Extra safety
        if (!topicId || !roadmapId || !day) {
          console.error("Invalid numeric values:", {
            topicId,
            roadmapId,
            day,
          });

          alert("Invalid parameters. Please try again.");
          router.replace("/dashboard/roadmap");
          return;
        }

        console.log("Creating mock test with:", {
          topicId,
          roadmapId,
          day,
        });

        // ✅ API call
        const data = await createMockTest({
          topic_id: topicId,
          roadmap_id: roadmapId,
          day,
          num_questions: 10,
        });

        // ✅ Ensure response is valid
        if (!data?.mock_test?.id) {
          throw new Error("Invalid response from server");
        }

        // ✅ Redirect to attempt page
        router.replace(`/dashboard/mocktest/${data.mock_test.id}`);

      } catch (error) {
        console.error("Mock test creation failed:", error);

        alert("Failed to start test. Please try again.");

        router.replace("/dashboard/roadmap");
      }
    };

    init();
  }, [params, router]);

  return (
    <div className="p-6">
      Starting test...
    </div>
  );
}