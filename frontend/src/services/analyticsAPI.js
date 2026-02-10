import api from './api';

function parseFilename(contentDisposition) {
  if (!contentDisposition) return '';
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) return decodeURIComponent(utf8Match[1]);
  const plainMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  if (plainMatch?.[1]) return plainMatch[1];
  return '';
}

export const getPortfolioAnalytics = async (portfolioId) => {
  const response = await api.get(`/api/v1/analytics/portfolios/${portfolioId}`);
  return response.data;
};

export const exportPortfolioAnalyticsCsv = async (portfolioId, report = 'summary') => {
  const response = await api.get(`/api/v1/analytics/portfolios/${portfolioId}/export`, {
    params: { report },
    responseType: 'blob',
  });
  const filename = parseFilename(response.headers?.['content-disposition']);
  return {
    blob: response.data,
    filename: filename || `portfolio_${portfolioId}_${report}.csv`,
  };
};

export default {
  getPortfolioAnalytics,
  exportPortfolioAnalyticsCsv,
};
