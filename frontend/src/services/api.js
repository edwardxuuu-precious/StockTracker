import axios from 'axios';
import API_CONFIG from '../config/config';

// Validate API URL on startup
const validateAPIUrl = (url) => {
  if (!url) {
    throw new Error('API URL is not configured. Please set VITE_API_URL in .env file.');
  }

  if (url.includes(':8000')) {
    console.error(
      '❌ CONFIGURATION ERROR: API is set to port 8000, but backend runs on port 8001!\n' +
      '   Please update VITE_API_URL in frontend/.env to: http://localhost:8001\n' +
      '   Then restart the frontend server: npm run dev'
    );
  }

  return url;
};

const API_BASE_URL = validateAPIUrl(API_CONFIG.baseURL);

console.log('🌐 API Client initialized with baseURL:', API_BASE_URL);

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
    // You can add auth tokens here later
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle errors globally with detailed diagnostics
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error - Cannot connect to API server');
      console.error('📍 Attempted URL:', error.config?.baseURL || API_BASE_URL);
      console.error('💡 Troubleshooting:');
      console.error('   1. Check if backend server is running: curl http://localhost:8001/api/v1/portfolios/');
      console.error('   2. Verify VITE_API_URL in frontend/.env is set to: http://localhost:8001');
      console.error('   3. Restart frontend server after changing .env: npm run dev');
      console.error('   4. Check backend logs for errors');
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;
