import { apiClient } from '@/lib/apiClient';

interface CreateMockTestPayload {
  topic_id?: number;
  roadmap_id?: number;
  day?: number;
  num_questions?: number;
  difficulty?: string;
}

interface SubmitAnswerPayload {
  attempt_id: number;
  question_id: number;
  user_answer: string;
  time_taken_seconds: number;
}

interface FinalizeTestPayload {
  attempt_id: number;
}

interface GeneratePracticePayload {
  topic_id: number;
  num_questions?: number;
}

export const getQuestions = async () => {
  const { data } = await apiClient.get('/questions/');
  return data;
};

export const createMockTest = async (payload: CreateMockTestPayload) => {
  const { data } = await apiClient.post('/mocktest/generate/', payload);
  return data;
};

export const getMockTestDetail = async (id: number) => {
  const { data } = await apiClient.get(`/mocktest/${id}/`);
  return data;
};

export const submitAnswer = async (payload: SubmitAnswerPayload) => {
  const { data } = await apiClient.post('/mocktest/submit-answer/', payload);
  return data;
};

export const getResults = async () => {
  const { data } = await apiClient.get('/mocktest/results/');
  return data;
};

export const finalizeTest = async (payload: FinalizeTestPayload) => {
  const { data } = await apiClient.post('/mocktest/results/', payload);
  return data;
};

export const getResultDetail = async (id: number) => {
  const { data } = await apiClient.get(`/mocktest/results/${id}/`);
  return data;
};

export const generatePractice = async (payload: GeneratePracticePayload) => {
  const { data } = await apiClient.post('/mocktest/generate-practice/', payload);
  return data;
};

export const explainQuestion = async (question_id: number) => {
  const { data } = await apiClient.post('/mocktest/explain/', { question_id });
  return data;
};
