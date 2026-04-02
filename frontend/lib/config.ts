/**
 * Application configuration
 */

export const config = {
  // API Configuration
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 30000, // 30 seconds
  },

  // Storage Keys
  storage: {
    token: 'nomadiq_token',
    user: 'nomadiq_user',
  },

  // Feature Flags
  features: {
    aiChat: true,
    guides: true,
    itinerary: true,
  },
}

export default config
