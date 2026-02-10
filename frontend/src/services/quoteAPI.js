import api from './api';

export const getQuote = async (symbol, options = {}) => {
  const response = await api.get(`/api/v1/quotes/${symbol}`, {
    params: {
      refresh: options.refresh ?? false,
    },
  });
  return response.data;
};

export const getBatchQuotes = async (symbols, options = {}) => {
  const normalized = (symbols || [])
    .map((item) => String(item || '').trim().toUpperCase())
    .filter(Boolean);

  if (normalized.length === 0) return [];

  const response = await api.get('/api/v1/quotes/batch', {
    params: {
      symbols: normalized.join(','),
      refresh: options.refresh ?? false,
    },
  });
  return response.data;
};

export default {
  getQuote,
  getBatchQuotes,
};
