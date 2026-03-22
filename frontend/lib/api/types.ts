// Authentication Types
export interface AuthRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
}

// Trip Types
export interface Trip {
  trip_id: string;
  user_id: string;
  destination: string;
  start_date: string;
  end_date: string;
  theme: string;
  budget: number | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateTripRequest {
  destination: string;
  start_date: string;
  end_date: string;
  theme: string;
  budget?: number | null;
  description?: string | null;
}

export interface UpdateTripRequest {
  destination?: string;
  start_date?: string;
  end_date?: string;
  theme?: string;
  budget?: number | null;
  description?: string | null;
}

// Itinerary Types
export interface ItineraryItem {
  item_id: string;
  trip_id: string;
  day: number;
  activity: string;
  location: string;
  start_time: string | null;
  end_time: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateItineraryItemRequest {
  trip_id: string;
  day: number;
  activity: string;
  location: string;
  start_time?: string | null;
  end_time?: string | null;
  notes?: string | null;
}

export interface UpdateItineraryItemRequest {
  day?: number;
  activity?: string;
  location?: string;
  start_time?: string | null;
  end_time?: string | null;
  notes?: string | null;
}

// Aliases for backward compatibility
export type ItineraryDay = ItineraryItem;
export type ItineraryActivity = ItineraryItem;
export type CreateActivityRequest = CreateItineraryItemRequest;

// Chat Types
export interface ChatMessage {
  message_id: string;
  trip_id: string;
  sender: 'user' | 'ai';
  message: string;
  created_at: string;
}

export interface SendMessageRequest {
  message: string;
}

// Travel Guide Types
export interface TravelGuide {
  guide_id: string;
  destination: string;
  title: string;
  description: string;
  duration_days: number;
  best_time: string;
  highlights: string | null;
  local_tips: string | null;
  created_at: string;
  updated_at: string;
}

export type Guide = TravelGuide;

// Recommendation Types
export interface Recommendation {
  id: string;
  trip_id: string;
  type: 'activity' | 'restaurant' | 'accommodation' | 'attraction';
  title: string;
  description: string;
  location: string;
  rating: number;
  price_range: string;
  created_at: string;
}

// API Error Response
export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, unknown>;
}

// Pagination Types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
