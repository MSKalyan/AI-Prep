'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from '@/features/auth';
import { CreateRoadmapForm } from '@/features/roadmap';

export default function RoadmapPage() {
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
    <div className="px-4 sm:px-6 py-6">
      <CreateRoadmapForm />
    </div>
  );
}
