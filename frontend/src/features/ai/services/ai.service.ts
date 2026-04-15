import { apiClient } from '@/lib/apiClient';

export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post('/documents/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const getDocuments = async () => {
  const { data } = await apiClient.get('/documents/');
  return data;
};

export const deleteDocument = async (id: number) => {
  await apiClient.delete(`/documents/${id}/`);
};

export const processDocuments = async () => {
  const { data } = await apiClient.post('/documents/process/');
  return data;
};

export const askAI = async (payload: {
  question: string;
  context?: string;
  conversation_id?: number;
}) => {
  const { data } = await apiClient.post('/ask-ai/', payload);
  return data;
};

export const getConversationMessages = async (conversationId: number) => {
  const { data } = await apiClient.get(`/conversations/${conversationId}/messages/`);
  return data;
};
