import api from './api';

export const createChatSession = async () => {
  const response = await api.post('/api/v1/chat/sessions');
  return response.data;
};

export const getChatMessages = async (sessionId, params = {}) => {
  const response = await api.get(`/api/v1/chat/sessions/${sessionId}/messages`, { params });
  return response.data;
};

export const postChatMessage = async (sessionId, payload) => {
  const response = await api.post(`/api/v1/chat/sessions/${sessionId}/messages`, payload);
  return response.data;
};

export default {
  createChatSession,
  getChatMessages,
  postChatMessage,
};
