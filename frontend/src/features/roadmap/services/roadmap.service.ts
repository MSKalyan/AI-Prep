import { apiClient } from "@/lib/apiClient";

/* ======================
   TYPES
====================== */

export interface DeterministicRoadmapPayload {
  exam_id: number;
  target_date: string;
  study_hours_per_day: number;
}

export interface DeterministicRoadmapResponse {
  roadmap_id: number;
  total_weeks: number;
  message: string;
}

/* ======================
   EXAMS
====================== */

export const getExams = async () => {
  const { data } = await apiClient.get("/exams/");
  return data;
};

/* ======================
   GENERATE ROADMAP (DETERMINISTIC - Sprint 3)
====================== */

export const generateRoadmap = async (
  payload: DeterministicRoadmapPayload
): Promise<DeterministicRoadmapResponse> => {
  const { data } = await apiClient.post(
    "/roadmap/generate/",
    payload
  );

  return data;
};

/* ======================
   ROADMAP LIST
====================== */

export const getRoadmaps = async () => {
  const { data } = await apiClient.get("/roadmaps/");
  return data;
};

/* ======================
   ROADMAP DETAIL
====================== */

export const getRoadmapDetail = async (id: number) => {
  const { data } = await apiClient.get(`/roadmap/${id}/`);
  return data;
};

export const deleteRoadmap = async (id: number) => {
  await apiClient.delete(`/roadmap/${id}/`);
};