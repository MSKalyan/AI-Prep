import { apiClient } from "@/lib/apiClient";

export interface StudyTopicResponse {
  roadmap_id: number;
  topic: string;
  subject: string;
  week: number;
  phase: string;
  estimated_hours: number;
  ai_explanation: string | null;
}

export interface SidebarTopic {
  id: number;
  topic: string;
  week: number;
  completed: boolean;
}

export interface TopicExplanationResponse {
  ai_explanation: string;
}

export async function getTopicStudy(topicId: number): Promise<StudyTopicResponse> {
  const res = await apiClient.get(`/roadmap/topics/${topicId}/study/`);
  return res.data;
}

export async function getTopicExplanation(
  topicId: number
): Promise<TopicExplanationResponse> {

  const res = await apiClient.get(`/roadmap/topics/${topicId}/explanation/`, {
  });

  return res.data;
}

export async function getRoadmapTopics(
  roadmapId: number
): Promise<SidebarTopic[]> {

  const res = await apiClient.get(`/roadmap/${roadmapId}/topics/`);
  return res.data;
}