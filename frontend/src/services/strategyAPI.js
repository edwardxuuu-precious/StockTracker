import api from './api';

export const getStrategies = async (limit = 100) => {
  const response = await api.get('/api/v1/strategies/', {
    params: { limit },
  });
  return response.data;
};

export const getStrategy = async (id) => {
  const response = await api.get(`/api/v1/strategies/${id}`);
  return response.data;
};

export const createStrategy = async (payload) => {
  const response = await api.post('/api/v1/strategies/', payload);
  return response.data;
};

export const updateStrategy = async (id, payload) => {
  const response = await api.put(`/api/v1/strategies/${id}`, payload);
  return response.data;
};

export default {
  getStrategies,
  getStrategy,
  createStrategy,
  updateStrategy,
};
