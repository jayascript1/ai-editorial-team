// AI Service for communicating with the backend API
// Handles all API calls to the Flask backend running on Vercel

// Get the base URL for API calls
const getBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // In browser - use current origin for production, localhost for development
    return window.location.hostname === 'localhost' 
      ? 'http://localhost:5001'
      : window.location.origin;
  }
  return '';
};

const BASE_URL = getBaseUrl();

export const aiService = {
  async generateContent(topic) {
    try {
      const response = await fetch(`${BASE_URL}/api/generate-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return {
        success: true,
        ...data
      };
    } catch (error) {
      console.error('Error generating content:', error);
      return {
        success: false,
        error: error.message
      };
    }
  },

  async getProcessStatus() {
    try {
      const response = await fetch(`${BASE_URL}/api/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting process status:', error);
      return {
        error: error.message
      };
    }
  },

  async getHealthCheck() {
    try {
      const response = await fetch(`${BASE_URL}/api/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error checking health:', error);
      return {
        error: error.message
      };
    }
  },

  // Create an EventSource for real-time updates
  createEventSource() {
    try {
      return new EventSource(`${BASE_URL}/api/stream`);
    } catch (error) {
      console.error('Error creating EventSource:', error);
      return null;
    }
  }
}

export default aiService
