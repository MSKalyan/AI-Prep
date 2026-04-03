import { useQuery } from "@tanstack/react-query";
import {
  fetchPerformance,
  fetchStudyPlan,
  fetchDashboardStats,
  PerformanceResponse
} from "../services/analytics.services";

import {apiClient }from "@/lib/apiClient";
/* ================= HOOKS ================= */

export const usePerformance = () => {
  return useQuery<PerformanceResponse>({
    queryKey: ["performance"],
      queryFn: async () => {
      const res = await apiClient.get("/analytics/performance/");
      return res.data.data; // ✅ must match PerformanceResponse
    },
  });
};

export const useStudyPlan = () => {
  return useQuery({
    queryKey: ["study-plan"],
    queryFn: fetchStudyPlan,
  });
};

export const useDashboardStats = (enabled:boolean) => {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboardStats,
    enabled,
  });
};

export const useAnalyticsSummary = () => {
  return useQuery({
    queryKey: ["analytics-summary"],
    queryFn: async () => {
      const res = await apiClient.get("/analytics/");
      return res.data;
    },
  });
};


export const useAdaptiveStudyPlan = () => {
  return useQuery({
    queryKey: ["adaptive-study-plan"],
    queryFn: async () => {
      const res = await apiClient.get("/analytics/adaptive-study-plan/");
      return res.data.data;
    },
  });
};

export const useTodayPlan = () => {
  return useQuery({
    queryKey: ["today-plan"],
    queryFn: async () => {
      const res = await apiClient.get("/analytics/adaptive-study-plan/");
      return res.data.data;
    },
  });
};