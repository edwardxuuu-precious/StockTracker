/**
 * Application Configuration
 * Centralized configuration management with validation
 */

// API Configuration
export const API_CONFIG = {
  // Base URL for API requests
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001',

  // Timeout for API requests (ms)
  timeout: 30000,

  // Retry configuration
  retry: {
    maxRetries: 3,
    retryDelay: 1000,
  },
};

// Environment validation
export const validateConfig = () => {
  const errors = [];

  // Validate API URL
  if (!API_CONFIG.baseURL) {
    errors.push('API_CONFIG.baseURL is not defined');
  }

  // Check if API URL is accessible
  if (API_CONFIG.baseURL.includes(':8000')) {
    console.warn(
      '⚠️  WARNING: API is configured to use port 8000. ' +
      'The backend server runs on port 8001. ' +
      'Please update VITE_API_URL in .env file to http://localhost:8001'
    );
  }

  // Log configuration in development
  if (import.meta.env.DEV) {
    console.log('🔧 API Configuration:', {
      baseURL: API_CONFIG.baseURL,
      environment: import.meta.env.MODE,
    });
  }

  return errors;
};

// Validate on module load
const configErrors = validateConfig();
if (configErrors.length > 0) {
  console.error('❌ Configuration errors:', configErrors);
}

export default API_CONFIG;
