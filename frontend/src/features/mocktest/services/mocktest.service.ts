import { apiClient } from "@/lib/apiClient";

export const getQuestions = async () => {
  const { data } = await apiClient.get("/questions/");
  return data;
};

export const createMockTest = async (payload: any) => {
  const { data } = await apiClient.post("/mocktest/generate/", payload);
  return data;
};

export const getMockTestDetail = async (id: number) => {
  const { data } = await apiClient.get(`/mocktest/${id}/`);
  return data;
};

export const submitAnswer = async (payload: any) => {
  const { data } = await apiClient.post("/mocktest/submit-answer/", payload);
  return data;
};

export const getResults = async () => {
  const { data } = await apiClient.get("/mocktest/results/");
  return data;
};

export const finalizeTest = async (payload: any) => {
  const { data } = await apiClient.post("/mocktest/results/", payload);
  return data;
};

export const getResultDetail = async (id: number) => {
  const { data } = await apiClient.get(`/mocktest/results/${id}/`);
  return data;
};

export const generatePractice = async (payload: any) => {
  const { data } = await apiClient.post("/mocktest/generate-practice/", payload);
  return data;
};

export const explainQuestion = async (question_id: number) => {
  const { data } = await apiClient.post("/mocktest/explain/", { question_id });
  return data;
};
