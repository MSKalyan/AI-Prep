"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useAuth } from "@/features/auth";
import { createMockTest } from "@/features/mocktest/services";

/* -------------------- AUTH WRAPPER -------------------- */
function MockTestPageContent() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login");
    }
  }, [user, authLoading, router]);

  if (authLoading) {
    return <div className="p-10 text-center">Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return (
    <Suspense fallback={<div className="p-4 sm:p-6">Loading...</div>}>
      <MockTestContent />
    </Suspense>
  );
}

/* -------------------- INNER CLIENT COMPONENT -------------------- */
function MockTestContent() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const init = async () => {
      try {
        const topicIdRaw = params.get("topicId");
        const roadmapIdRaw = params.get("roadmapId");
        const dayRaw = params.get("day");

        // Validate params
        if (!topicIdRaw || !roadmapIdRaw || !dayRaw) {
          console.error("Missing params", {
            topicIdRaw,
            roadmapIdRaw,
            dayRaw,
          });
          router.replace("/dashboard");
          return;
        }

        const topicId = Number(topicIdRaw);
        const roadmapId = Number(roadmapIdRaw);
        const day = Number(dayRaw);

        if (!topicId || !roadmapId || !day) {
          console.error("Invalid numeric params", {
            topicId,
            roadmapId,
            day,
          });
          router.replace("/dashboard");
          return;
        }

        const data = await createMockTest({
          topic_id: topicId,
          roadmap_id: roadmapId,
          day,
          num_questions: 10,
        });

        if (!data?.mock_test?.id) {
          throw new Error("Invalid response");
        }

        router.replace(`/dashboard/mocktest/${data.mock_test.id}`);
      } catch (error) {
        console.error("Mock test creation failed:", error);
        router.replace("/dashboard");
      }
    };

    init();
  }, [params, router]);

  return <div className="p-4 sm:p-6">Starting test...</div>;
}

/* -------------------- PAGE (WRAPPER) -------------------- */

export const dynamic = "force-dynamic";

export default function MockTestPage() {
  return <MockTestPageContent />;
}