import api from './api';

export const runBacktest = async (payload) => {
  const response = await api.post('/api/v1/backtests/', payload);
  return response.data;
};

export const getBacktests = async (params = {}) => {
  const response = await api.get('/api/v1/backtests/', { params });
  return response.data;
};

export const getBacktest = async (id) => {
  const response = await api.get(`/api/v1/backtests/${id}`);
  return response.data;
};

export const getBacktestTrades = async (id) => {
  const response = await api.get(`/api/v1/backtests/${id}/trades`);
  return response.data;
};

export default {
  runBacktest,
  getBacktests,
  getBacktest,
  getBacktestTrades,
};
