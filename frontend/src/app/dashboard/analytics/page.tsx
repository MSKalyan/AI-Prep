'use client';

import { useRequireAuth } from '@/features/auth';
import { usePerformance, useAnalyticsSummary, useAnalyticsComputed } from '@/features/analytics';
import { Section } from '@/features/analytics/components';

export default function AnalyticsPageImproved() {
  const { user, isLoading: authLoading } = useRequireAuth();

  const { data, isLoading } = usePerformance();
  const { data: summary } = useAnalyticsSummary();

  const topics = data?.topics || [];
  const { weak, moderate, strong, avgAccuracy, avgTime } = useAnalyticsComputed(topics);

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Loading analytics...
      </div>
    );
  }

  if (!user) return null;

  const totalMocktests = summary?.total_mocktests || 0;
  const totalQuestions = summary?.total_questions_attempted || 0;

  return (
    <div className="min-h-screen bg-gray-100 text-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* HEADER */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Analytics Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">
              Performance insights, accuracy trends, and weak areas
            </p>
          </div>
        </div>

        {/* KPI CARDS */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white rounded-2xl shadow p-5">
            <p className="text-sm text-gray-500">Mock Tests</p>
            <p className="text-2xl font-semibold">{totalMocktests}</p>
          </div>

          <div className="bg-white rounded-2xl shadow p-5">
            <p className="text-sm text-gray-500">Questions Attempted</p>
            <p className="text-2xl font-semibold">{totalQuestions}</p>
          </div>

          <div className="bg-white rounded-2xl shadow p-5">
            <p className="text-sm text-gray-500">Avg Accuracy</p>
            <p className="text-2xl font-semibold text-green-600">
              {(avgAccuracy * 100).toFixed(1)}%
            </p>
          </div>

          <div className="bg-white rounded-2xl shadow p-5">
            <p className="text-sm text-gray-500">Avg Time / Question</p>
            <p className="text-2xl font-semibold">{avgTime.toFixed(1)} sec</p>
          </div>
        </div>

        {/* PERFORMANCE DISTRIBUTION */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Performance Distribution</h2>

          <div className="flex h-4 rounded overflow-hidden">
            <div className="bg-red-500" style={{ width: `${weak.length * 10}%` }} />
            <div className="bg-yellow-400" style={{ width: `${moderate.length * 10}%` }} />
            <div className="bg-green-500" style={{ width: `${strong.length * 10}%` }} />
          </div>

          <div className="flex justify-between text-xs mt-2 text-gray-600">
            <span>Weak ({weak.length})</span>
            <span>Moderate ({moderate.length})</span>
            <span>Strong ({strong.length})</span>
          </div>
        </div>

        {/* WEAK TOPICS */}
        <div className="bg-white rounded-2xl shadow p-6">
          <Section title="Weak Topics" data={weak} emptyText="No weak topics — good progress" />
        </div>

        {/* MODERATE + STRONG (OPTIONAL BUT IMPORTANT) */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl shadow p-6">
            <Section title="Moderate Topics" data={moderate} emptyText="No moderate topics" />
          </div>

          <div className="bg-white rounded-2xl shadow p-6">
            <Section title="Strong Topics" data={strong} emptyText="No strong topics yet" />
          </div>
        </div>
      </div>
    </div>
  );
}
