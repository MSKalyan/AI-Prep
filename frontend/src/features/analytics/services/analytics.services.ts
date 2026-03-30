import { apiClient } from "@/lib/apiClient";

/* ================= TYPES ================= */

export type TopicPerformance = {
  topic_id: number;
  topic_name:string;
  accuracy: number;
  avg_time: number;
  total_attempts: number;
  strength: "weak" | "moderate" | "strong" | "insufficient";
};

export type PerformanceResponse = {
  topics: TopicPerformance[];
  total_mocktests: number;
  total_questions_attempted: number;
};
export type StudyPlanItem = {
  topic_id: number;
  topic_name:string;
  priority: number;
  suggested_time_minutes: number;
  strength: "weak" | "moderate" | "strong" | "insufficient";
};

export type DashboardStats = {
  study_streak: number;
  topics_completed: number;
  roadmap_progress: number;
  average_score: number;
  continue_studying?: {
    topic_id: number;
    topic_name: string;
  };
  roadmaps: Array<{
    id: number;
    exam_name: string;
    is_active: boolean;
  }>;
};

/* ================= API CALLS ================= */

export const fetchPerformance = async (): Promise<TopicPerformance[]> => {
  const res = await apiClient.get("/analytics/performance/");
  return res.data.data;
};

export const fetchStudyPlan = async (): Promise<StudyPlanItem[]> => {
  const res = await apiClient.get("/analytics/adaptive-study-plan/");
  return res.data.data;
};

export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const res = await apiClient.get("/analytics/dashboard/");
  return res.data;
};