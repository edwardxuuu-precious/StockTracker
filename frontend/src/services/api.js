import axios from 'axios';
import API_CONFIG from '../config/config';

// Validate API URL on startup
const validateAPIUrl = (url) => {
  if (!url) {
    throw new Error('API URL is not configured. Please set VITE_API_URL in frontend/.env.');
  }

  try {
    new URL(url);
  } catch {
    throw new Error(`API URL is invalid: ${url}`);
  }

  return url;
};

const API_BASE_URL = validateAPIUrl(API_CONFIG.baseURL);

if (import.meta.env.DEV) {
  console.log('[api] Client initialized with baseURL:', API_BASE_URL);
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here later.
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      const baseUrl = error.config?.baseURL || API_BASE_URL;
      const probeUrl = `${String(baseUrl).replace(/\/$/, '')}/api/v1/portfolios/`;
      console.error('Network Error - Cannot connect to API server');
      console.error('Attempted URL:', baseUrl);
      console.error('Troubleshooting:');
      console.error(`  1. Check backend server: curl ${probeUrl}`);
      console.error('  2. Verify VITE_API_URL in frontend/.env');
      console.error('  3. Restart frontend after changing .env: npm run dev');
      console.error('  4. Check backend logs for errors');
    } else {
      console.error('Error:', error.message);
    }

    return Promise.reject(error);
  }
);

export default api;

