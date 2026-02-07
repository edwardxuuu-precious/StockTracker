/**
 * Health Check Utility
 * Validates that the API server is accessible before the app starts
 */

import API_CONFIG from '../config/config';

/**
 * Check if API server is responding
 */
export const checkAPIHealth = async () => {
  const healthCheckUrl = `${API_CONFIG.baseURL}/docs`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(healthCheckUrl, {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      console.log('✅ API Health Check: Backend server is running');
      return { healthy: true };
    } else {
      console.warn('⚠️  API Health Check: Backend returned status', response.status);
      return { healthy: false, status: response.status };
    }
  } catch (error) {
    console.error('❌ API Health Check Failed');
    console.error('📍 Attempted to connect to:', API_CONFIG.baseURL);

    if (error.name === 'AbortError') {
      console.error('⏱️  Connection timeout - Backend server is not responding');
    } else {
      console.error('🔌 Cannot connect to backend server');
    }

    console.error('\n💡 Troubleshooting Steps:');
    console.error('1. Check if backend is running:');
    console.error('   - Run: start-backend.bat');
    console.error('   - Or: cd backend && python start_server.py --port 8001');
    console.error('\n2. Verify backend URL in frontend/.env:');
    console.error('   VITE_API_URL=http://localhost:8001');
    console.error('\n3. Test backend directly:');
    console.error('   curl http://localhost:8001/api/v1/portfolios/');
    console.error('\n4. Check for port conflicts:');
    console.error('   netstat -ano | findstr :8001');

    return { healthy: false, error: error.message };
  }
};

/**
 * Display API connection status in UI
 */
export const getConnectionStatus = () => {
  return {
    baseURL: API_CONFIG.baseURL,
    configured: !!API_CONFIG.baseURL,
    expectedPort: '8001',
    actualPort: API_CONFIG.baseURL.match(/:(\d+)/)?.[1] || 'unknown',
  };
};
