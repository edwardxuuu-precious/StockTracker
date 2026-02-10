import api from './api';

export const generateStrategyByPrompt = async (payload) => {
  const response = await api.post('/api/v1/agent/strategy/generate', payload);
  return response.data;
};

export const tuneStrategyByAgent = async (payload) => {
  const response = await api.post('/api/v1/agent/strategy/tune', payload);
  return response.data;
};

export const buildBacktestReportByAgent = async (backtestId, payload) => {
  const response = await api.post(`/api/v1/agent/backtests/${backtestId}/report`, payload);
  return response.data;
};

export default {
  generateStrategyByPrompt,
  tuneStrategyByAgent,
  buildBacktestReportByAgent,
};
