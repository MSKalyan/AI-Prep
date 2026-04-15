export {
  usePerformance,
  useStudyPlan,
  useDashboardStats,
  useAnalyticsSummary,
  useAdaptiveStudyPlan,
  useTodayPlan,
} from './hooks/useAnalytics';
export { useAnalyticsComputed } from './hooks/useAnalyticsComputed';

export { default as StatCard } from './components/StatCard';
export { default as Section } from './components/Section';

export * from './services/analytics.service';
