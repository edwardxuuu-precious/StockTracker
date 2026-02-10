import api from './api';

export const listStrategyVersions = async (strategyId) => {
  const response = await api.get(`/api/v1/strategies/${strategyId}/versions`);
  return response.data;
};

export const createStrategyVersion = async (strategyId, payload) => {
  const response = await api.post(`/api/v1/strategies/${strategyId}/versions`, payload);
  return response.data;
};

export const compareStrategyVersions = async (payload) => {
  const response = await api.post('/api/v1/strategies/versions/compare', payload);
  return response.data;
};

export default {
  listStrategyVersions,
  createStrategyVersion,
  compareStrategyVersions,
};
