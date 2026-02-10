import api from './api';

export const getMarketDataStatus = async (params) => {
  const response = await api.get('/api/v1/market-data/status', { params });
  return response.data;
};

export const getIngestionLogs = async (params) => {
  const response = await api.get('/api/v1/market-data/ingestions', { params });
  return response.data;
};

export const runIngestion = async (payload) => {
  const response = await api.post('/api/v1/market-data/ingest', payload);
  return response.data;
};

export default {
  getMarketDataStatus,
  getIngestionLogs,
  runIngestion,
};
