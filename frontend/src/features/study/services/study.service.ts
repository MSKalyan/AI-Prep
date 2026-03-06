import { apiClient } from "@/lib/apiClient";

export interface StudyTopicResponse {
  roadmap_id:number;
  topic: string;
  subject: string;
  week: number;
  phase: string;
  estimated_hours: number;
  ai_explanation: string;
}

export interface SidebarTopic {
  id: number;
  topic: string;
  week: number;
  completed: boolean;
}


export async function getTopicStudy(topicId: number): Promise<StudyTopicResponse> {
  const res = await apiClient.get(`/roadmap/topics/${topicId}/study/`);
  return res.data;
}

export async function getTopicExplanation(topicId: number): Promise<{ explanation: string }> {
  const res = await apiClient.post(`/ai/explain-topic/`, {
    topic_id: topicId,
  });

  return res.data;
}

export async function getRoadmapTopics(
  roadmapId: number
) {

  const res = await apiClient.get(
    `/roadmap/${roadmapId}/topics/`
  );

  return res.data;
}