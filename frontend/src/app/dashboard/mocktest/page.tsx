'use client';

import { useEffect, Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/features/auth';
import { createMockTest } from '@/features/mocktest/services';

/* -------------------- AUTH WRAPPER -------------------- */
function MockTestPageContent() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace('/login');
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
  const [isCreating, setIsCreating] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  const topicIdRaw = params.get('topicId');
  const roadmapIdRaw = params.get('roadmapId');
  const dayRaw = params.get('day');

  useEffect(() => {
    const init = async () => {
      setIsCreating(true);
      setErrorMessage('');
      try {
        if (!topicIdRaw || !roadmapIdRaw || !dayRaw) {
          router.replace('/dashboard');
          return;
        }

        const topicId = Number(topicIdRaw);
        const roadmapId = Number(roadmapIdRaw);
        const day = Number(dayRaw);

        if (!topicId || !roadmapId || !day) {
          router.replace('/dashboard');
          return;
        }

        const data = await createMockTest({
          topic_id: topicId,
          roadmap_id: roadmapId,
          day,
          num_questions: 10,
        });

        if (!data?.mock_test?.id) {
          throw new Error('Failed to create mock test');
        }

        if (!data.mock_test.question_count) {
          throw new Error('No questions available for this topic. Please try a different topic or day.');
        }

        router.replace(`/dashboard/mocktest/${data.mock_test.id}`);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : 'Unexpected error occurred';
        setErrorMessage(message);
      } finally {
        setIsCreating(false);
      }
    };

    init();
  }, [topicIdRaw, roadmapIdRaw, dayRaw, router]);

  if (isCreating) {
    return <div className="p-4 sm:p-6">Starting test...</div>;
  }

  if (errorMessage) {
    return (
      <div className="p-4 sm:p-6 space-y-3">
        <div className="text-sm text-red-600">{errorMessage}</div>
        <button
          onClick={() => router.replace('/dashboard')}
          className="px-4 py-2 bg-black text-white rounded"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return <div className="p-4 sm:p-6">Redirecting...</div>;
}

/* -------------------- PAGE (WRAPPER) -------------------- */

export const dynamic = 'force-dynamic';

export default function MockTestPage() {
  return <MockTestPageContent />;
}
