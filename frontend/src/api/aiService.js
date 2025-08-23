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
      const productionUrl = 'https://ai-editorial-team.onrender.com';
      console.log('🔧 Using production API URL:', productionUrl);
      return productionUrl;
    }
  }
  return '';
};

const BASE_URL = getBaseUrl();
console.log('🚀 AI Service initialized with BASE_URL:', BASE_URL);

// Store user_id globally for EventSource
let currentUserId = null;

export const aiService = {
  async generateContent(topic) {
    try {
      console.log('📡 Making request to:', `${BASE_URL}/api/generate-content`);
      const response = await fetch(`${BASE_URL}/api/generate-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for session management
        body: JSON.stringify({ topic })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API Error Response:', response.status, errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      console.log('✅ Content generation started successfully');
      
      // Store the user_id for EventSource
      if (data.user_id) {
        currentUserId = data.user_id;
        console.log('🏷️ Stored user_id for EventSource:', data.user_id);
      }
      
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
      const response = await fetch(`${BASE_URL}/api/status`, {
        credentials: 'include' // Include cookies for session management
      });
      
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
      const response = await fetch(`${BASE_URL}/api/health`, {
        credentials: 'include' // Include cookies for session management
      });
      
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

  // Create an EventSource for real-time updates with user ID
  createEventSource() {
    try {
      // Use stored user_id if available, otherwise fallback to session-based
      const streamUrl = currentUserId 
        ? `${BASE_URL}/api/stream?user_id=${currentUserId}` 
        : `${BASE_URL}/api/stream`;
      
      console.log('📡 Creating EventSource for:', streamUrl);
      console.log('🔍 DEBUG: currentUserId =', currentUserId);
      
      // EventSource will automatically include cookies for same-origin requests
      const eventSource = new EventSource(streamUrl);
      
      return eventSource;
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
