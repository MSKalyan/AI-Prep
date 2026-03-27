import { useQuery } from "@tanstack/react-query";
import {
  fetchPerformance,
  fetchStudyPlan,
  fetchDashboardStats,
} from "../services/analytics.services";

/* ================= HOOKS ================= */

export const usePerformance = () => {
  return useQuery({
    queryKey: ["performance"],
    queryFn: fetchPerformance,
  });
};

export const useStudyPlan = () => {
  return useQuery({
    queryKey: ["study-plan"],
    queryFn: fetchStudyPlan,
  });
};

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboardStats,
  });
};