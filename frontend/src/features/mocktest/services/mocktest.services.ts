import { apiClient } from "@/lib/apiClient";

/* ======================
   QUESTIONS LIST
====================== */
export const getQuestions = async () => {
  const { data } = await apiClient.get("/questions/");
  return data;
};

/* ======================
   CREATE MOCK TEST
====================== */
export const createMockTest = async (payload:any) => {
  const { data } = await apiClient.post("/mocktest/generate/", payload);
  return data;
};

/* ======================
   MOCK TEST DETAIL
====================== */
export const getMockTestDetail = async (id:number) => {
  const { data } = await apiClient.get(`/mocktest/${id}/`);
  return data;
};

/* ======================
   SUBMIT ANSWER
====================== */
export const submitAnswer = async (payload:any) => {
  const { data } = await apiClient.post("/mocktest/submit-answer/", payload);
  return data;
};

/* ======================
   TEST RESULTS
====================== */
export const getResults = async () => {
  const { data } = await apiClient.get("/mocktest/results/");
  return data;
};

export const finalizeTest = async (payload:any) => {
  const { data } = await apiClient.post("/mocktest/results/", payload);
  return data;
};

/* ======================
   GENERATE PRACTICE
====================== */
export const generatePractice = async (payload:any) => {
  const { data } = await apiClient.post("/mocktest/generate-practice/", payload);
  return data;
};