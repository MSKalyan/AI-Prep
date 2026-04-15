import { apiClient } from '@/lib/apiClient';

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
  day_number?: number;
  subject: string;
  topic: string;
  hours: number;
  completed: boolean;
  is_completed?: boolean;
  phase: 'study' | 'revision' | 'practice';
}

export interface WeekProgress {
  week: number;
  total_topics: number;
  completed_topics: number;
  progress: number;
}

export interface RevisionItem {
  topic_id: number;
  topic_name: string;
  priority: number;
  roadmap_topic_id: number;
}

export interface WeekPlanResponse {
  data: WeekTopic[];
  today_revision: RevisionItem[];
}

export interface RoadmapListItem {
  id: number;
  exam?: { name: string };
  target_date: string;
}

export const getExams = async () => {
  const { data } = await apiClient.get('/exams/');
  return data;
};

export const generateRoadmap = async (
  payload: DeterministicRoadmapPayload
): Promise<DeterministicRoadmapResponse> => {
  const { data } = await apiClient.post('/roadmap/generate/', payload);
  return data;
};

export const getRoadmaps = async () => {
  const { data } = await apiClient.get('/roadmaps/');
  return data;
};

export const getRoadmapDetail = async (id: number) => {
  const { data } = await apiClient.get(`/roadmap/${id}/`);
  return data;
};

export const deleteRoadmap = async (id: number) => {
  await apiClient.delete(`/roadmap/${id}/`);
};

export const getWeekTopics = async (roadmapId: number, week: number): Promise<WeekPlanResponse> => {
  const { data } = await apiClient.get(`/roadmap/${roadmapId}/week/${week}/`);
  return data;
};

export const toggleTopic = async (topicId: number) => {
  const { data } = await apiClient.patch(`/roadmap/topic/${topicId}/complete/`);
  return data;
};

export const getWeekProgress = async (roadmapId: number, week: number): Promise<WeekProgress> => {
  const { data } = await apiClient.get(`/roadmap/${roadmapId}/week/${week}/progress/`);
  return data;
};

export const getRoadmapTopicExplanation = async (topicId: number) => {
  const { data } = await apiClient.get(`/roadmap/topic/${topicId}/explanation/`);
  return data;
};

export const getRoadmapProgress = async (roadmapId: number) => {
  const { data } = await apiClient.get(`/roadmap/${roadmapId}/progress/`);
  return data;
};
