// AI Service for communicating with the backend API
// Handles all API calls to the Flask backend running on Render

// Get the base URL for API calls
const getBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // Check for environment variable first
    const envApiUrl = import.meta.env.VITE_API_URL;
    if (envApiUrl) {
      console.log('🔧 Using environment API URL:', envApiUrl);
      return envApiUrl;
    }
    
    // Fallback logic for development vs production
    if (window.location.hostname === 'localhost') {
      console.log('🔧 Using localhost API URL for development');
      return 'http://localhost:5001';
    } else {
      // Production URL - should match your Render backend
      const productionUrl = 'https://ai-editorial-team-backend.onrender.com';
      console.log('🔧 Using production API URL:', productionUrl);
      return productionUrl;
    }
  }
  return '';
};

const BASE_URL = getBaseUrl();
console.log('🚀 AI Service initialized with BASE_URL:', BASE_URL);

export const aiService = {
  async generateContent(topic) {
    try {
      console.log('📡 Making request to:', `${BASE_URL}/api/generate-content`);
      const response = await fetch(`${BASE_URL}/api/generate-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API Error Response:', response.status, errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      console.log('✅ Content generation started successfully');
      return {
        success: true,
        ...data
      };
    } catch (error) {
      console.error('❌ Error generating content:', error);
      return {
        success: false,
        error: error.message
      };
    }
  },

  async getProcessStatus() {
    try {
      console.log('📡 Getting process status from:', `${BASE_URL}/api/status`);
      const response = await fetch(`${BASE_URL}/api/status`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Status API Error:', response.status, errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ Error getting process status:', error);
      return {
        error: error.message
      };
    }
  },

  async getHealthCheck() {
    try {
      console.log('📡 Health check from:', `${BASE_URL}/api/health`);
      const response = await fetch(`${BASE_URL}/api/health`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Health check failed:', response.status, errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      const healthData = await response.json();
      console.log('✅ Health check successful:', healthData);
      return healthData;
    } catch (error) {
      console.error('❌ Error checking health:', error);
      return {
        error: error.message
      };
    }
  },

  // Create an EventSource for real-time updates
  createEventSource() {
    try {
      const streamUrl = `${BASE_URL}/api/stream`;
      console.log('📡 Creating EventSource for:', streamUrl);
      return new EventSource(streamUrl);
    } catch (error) {
      console.error('❌ Error creating EventSource:', error);
      return null;
    }
  },

  // Test the API connection
  async testConnection() {
    try {
      console.log('🧪 Testing API connection to:', BASE_URL);
      const result = await this.getHealthCheck();
      if (result.error) {
        console.error('❌ API connection test failed:', result.error);
        return false;
      }
      console.log('✅ API connection test successful');
      return true;
    } catch (error) {
      console.error('❌ API connection test failed:', error);
      return false;
    }
  }
}

export default aiService
