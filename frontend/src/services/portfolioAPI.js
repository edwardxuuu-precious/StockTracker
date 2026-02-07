import api from './api';

// Get all portfolios
export const getPortfolios = async () => {
  const response = await api.get('/api/v1/portfolios/');
  return response.data;
};

// Get a specific portfolio
export const getPortfolio = async (id) => {
  const response = await api.get(`/api/v1/portfolios/${id}/`);
  return response.data;
};

// Create a new portfolio
export const createPortfolio = async (portfolioData) => {
  const response = await api.post('/api/v1/portfolios/', portfolioData);
  return response.data;
};

// Update a portfolio
export const updatePortfolio = async (id, portfolioData) => {
  const response = await api.put(`/api/v1/portfolios/${id}/`, portfolioData);
  return response.data;
};

// Delete a portfolio
export const deletePortfolio = async (id) => {
  await api.delete(`/api/v1/portfolios/${id}/`);
};

export default {
  getPortfolios,
  getPortfolio,
  createPortfolio,
  updatePortfolio,
  deletePortfolio,
};
