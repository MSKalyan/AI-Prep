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

export interface WeekTopic {
  id: number;
  day: number;
  subject: string;
  topic: string;
  hours: number;
  completed: boolean;
}

export interface WeekProgress {
  week: number;
  total_topics: number;
  completed_topics: number;
  progress: number;
}

/* ======================
   EXAMS
====================== */

export const getExams = async () => {
  const { data } = await apiClient.get("/exams/");
  return data;
};

/* ======================
   GENERATE ROADMAP
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

/* ======================
   WEEK TOPICS
====================== */

export const getWeekTopics = async (
  roadmapId: number,
  week: number
): Promise<WeekTopic[]> => {

  const { data } = await apiClient.get(
    `/roadmap/${roadmapId}/week/${week}/`
  );

  return data;
};

/* ======================
   TOGGLE TOPIC COMPLETE
====================== */

export const toggleTopic = async (topicId: number) => {

  const { data } = await apiClient.patch(
    `/roadmap/topic/${topicId}/complete/`
  );

  return data;
};

/* ======================
   WEEK PROGRESS
====================== */

export const getWeekProgress = async (
  roadmapId: number,
  week: number
): Promise<WeekProgress> => {

  const { data } = await apiClient.get(
    `/roadmap/${roadmapId}/week/${week}/progress/`
  );

  return data;
};

/* ======================
   AI EXPLANATION
====================== */

export const getTopicExplanation = async (topicId: number) => {

  const { data } = await apiClient.get(
    `/roadmap/topic/${topicId}/explanation/`
  );

  return data;
};

export const getRoadmapProgress = async (roadmapId: number) => {

const { data } = await apiClient.get(
    `/roadmap/${roadmapId}/progress/`
);

return data;
};