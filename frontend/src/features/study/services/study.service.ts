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
export type StudyContent = {
  topic_id: number;
  topic_name: string;
  description: string;
  youtube_links: string[];  // ✅ ADD THIS
};

export interface TopicExplanationResponse {
  ai_explanation: string;
}

export async function getTopicStudy(topicId: number) {
  // 1️⃣ Roadmap study API
  const studyRes = await apiClient.get(
    `/roadmap/topics/${topicId}/study/`
  );

  const studyData = studyRes.data;

  console.log("Study data:", studyData);

  // 🔥 IMPORTANT: extract REAL topic id
  const realTopicId = studyData.topic_id;

  try {
    // 2️⃣ Analytics API (USE REAL ID)
    const contentRes = await apiClient.get(
      `/analytics/study-content/${realTopicId}/`
    );

    console.log("YT RESPONSE:", contentRes.data);

    const contentData = contentRes.data.data;

    return {
      ...studyData,
      description: contentData.description,
      youtube_links: contentData.youtube_links,
      topic_name: contentData.topic_name,
    };

  } catch (err) {
    console.error("YT API FAILED:", err);

    return {
      ...studyData,
      description: "",
      youtube_links: [],
      topic_name: studyData.topic,
    };
  }
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