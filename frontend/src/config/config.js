/**
 * Application Configuration
 * Centralized configuration management with validation
 */

const DEFAULT_API_URL = 'http://localhost:8001';

// API Configuration
export const API_CONFIG = {
  // Base URL for API requests
  baseURL: (import.meta.env.VITE_API_URL || DEFAULT_API_URL).trim(),

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

  if (!API_CONFIG.baseURL) {
    errors.push('API_CONFIG.baseURL is not defined');
  }

  try {
    // Validate URL format early so startup errors are explicit.
    new URL(API_CONFIG.baseURL);
  } catch {
    errors.push(`API_CONFIG.baseURL is not a valid URL: ${API_CONFIG.baseURL}`);
  }

  if (import.meta.env.DEV) {
    console.log('[config] API configuration:', {
      baseURL: API_CONFIG.baseURL,
      environment: import.meta.env.MODE,
    });
  }

  return errors;
};

// Validate on module load
const configErrors = validateConfig();
if (configErrors.length > 0) {
  console.error('[config] Configuration errors:', configErrors);
}

export default API_CONFIG;

