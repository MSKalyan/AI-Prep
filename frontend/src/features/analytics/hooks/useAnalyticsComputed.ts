'use client';

import { TopicPerformance } from '../services/analytics.service';

export function useAnalyticsComputed(topics: TopicPerformance[]) {
  const weak = topics.filter((t) => t.strength === 'weak');
  const moderate = topics.filter((t) => t.strength === 'moderate');
  const strong = topics.filter((t) => t.strength === 'strong');

  const avgAccuracy =
    topics.length > 0 ? topics.reduce((sum, t) => sum + t.accuracy, 0) / topics.length : 0;

  const avgTime =
    topics.length > 0 ? topics.reduce((sum, t) => sum + t.avg_time, 0) / topics.length : 0;

  return { weak, moderate, strong, avgAccuracy, avgTime };
}
