import api from './api';

// Add a new holding to a portfolio
export const addHolding = async (portfolioId, holdingData) => {
  const response = await api.post(`/api/v1/portfolios/${portfolioId}/holdings`, holdingData);
  return response.data;
};

// Remove a holding from a portfolio
export const removeHolding = async (portfolioId, holdingId) => {
  await api.delete(`/api/v1/portfolios/${portfolioId}/holdings/${holdingId}`);
};

// Update a holding
export const updateHolding = async (portfolioId, holdingId, holdingData) => {
  const response = await api.put(`/api/v1/portfolios/${portfolioId}/holdings/${holdingId}`, holdingData);
  return response.data;
};

// Execute a BUY/SELL trade
export const executeTrade = async (portfolioId, tradeData) => {
  const response = await api.post(`/api/v1/portfolios/${portfolioId}/trades`, tradeData);
  return response.data;
};

// Get recent trade history
export const getTrades = async (portfolioId, limit = 50) => {
  const response = await api.get(`/api/v1/portfolios/${portfolioId}/trades`, {
    params: { limit },
  });
  return response.data;
};

export default {
  addHolding,
  removeHolding,
  updateHolding,
  executeTrade,
  getTrades,
};
