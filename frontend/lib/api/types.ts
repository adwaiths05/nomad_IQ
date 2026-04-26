export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, unknown>;
}

export interface User {
  id: string;
  email: string;
  name: string;
  username?: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  user: User;
}

export interface AuthRequest {
  email: string;
  password: string;
}

export interface Trip {
  id: string;
  user_id: string;
  group_id: string | null;
  city: string;
  start_date: string;
  end_date: string;
  budget_min: number;
  budget_max: number;
  flexibility_level: 'strict' | 'moderate' | 'light' | string;
  status: string;

  // Compatibility fields used by older pages.
  trip_id?: string;
  destination?: string;
  theme?: string;
  budget?: number | null;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface CreateTripRequest {
  user_id?: string;
  group_id?: string | null;
  city?: string;
  destination?: string;
  start_date: string;
  end_date: string;
  budget_min?: number;
  budget_max?: number;
  budget?: number | null;
  flexibility_level?: 'strict' | 'moderate' | 'light' | string;
  theme?: string;
  description?: string | null;
}

export interface UpdateTripRequest {
  city?: string;
  destination?: string;
  start_date?: string;
  end_date?: string;
  budget_min?: number;
  budget_max?: number;
  budget?: number | null;
  flexibility_level?: 'strict' | 'moderate' | 'light' | string;
  theme?: string;
  description?: string | null;
  status?: string;
}

export interface ItineraryItem {
  id: string;
  day_id: string;
  place_id: string | null;
  start_time: string | null;
  end_time: string | null;
  activity_type: string;
  travel_time_minutes: number;
  cost_estimate: number;
  confidence_score: string;
  source_type: string;

  // Compatibility fields used by older pages.
  item_id?: string;
  trip_id?: string;
  day?: number;
  activity?: string;
  location?: string;
  notes?: string | null;
  created_at?: string;
  updated_at?: string;
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
  start_time?: string | null;
  end_time?: string | null;
  activity_type?: string;
  travel_time_minutes?: number;
  cost_estimate?: number;
  confidence_score?: string;
  source_type?: string;
}

export interface ChatMessage {
  message_id: string;
  trip_id: string;
  sender: 'user' | 'ai';
  message: string;
  created_at: string;
}

export interface AmbientAssistRequest {
  query: string;
  trip_id?: string;
  user_id?: string;
  screen?: string;
  location_context?: string;
}

export interface QueryExpansionResponse {
  original_query: string;
  expanded_queries: string[];
  context_used: Record<string, unknown>;
}

export interface AmbientContextPacket {
  screen: string;
  generated_at: string;
  current_city?: string | null;
  current_itinerary_summary?: string | null;
  saved_preference_summary?: string | null;
  remaining_budget?: number | null;
  budget_currency: string;
  current_location_context?: string | null;
  live_transit_conditions?: string | null;
  active_disruptions: string[];
}

export interface AmbientProactiveCard {
  title: string;
  detail: string;
  action_label: string;
}

export interface ToolTraceRead {
  tool_name: string;
  summary: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

export interface MemorySearchResult {
  id: string;
  user_id?: string | null;
  group_id?: string | null;
  content: string;
  metadata: Record<string, unknown>;
  semantic_similarity: number;
  keyword_match: number;
  recency: number;
  score: number;
  matched_queries: string[];
  memory_type: string;
}

export interface AmbientProvenanceRead {
  memory_items: MemorySearchResult[];
  tool_traces: ToolTraceRead[];
}

export interface AmbientAssistResponse {
  answer: string;
  expanded_queries: string[];
  context_packet: AmbientContextPacket;
  confidence: number;
  uncertainty_note?: string | null;
  sources: string[];
  proactive_cards: AmbientProactiveCard[];
  memory_updated: boolean;
  provenance: AmbientProvenanceRead;
  debug?: Record<string, unknown>;
}

export interface SendMessageRequest {
  message: string;
}

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

export interface BudgetRead {
  id: string;
  trip_id: string;
  estimated_total: number;
  actual_spent: number;
  status: string;
  created_at?: string;
  updated_at?: string;
}

export interface WeatherRead {
  id?: string;
  city: string;
  date: string;
  weather: string;
  temperature_c?: number;
  payload?: Record<string, unknown>;
}

export interface EnvironmentRead {
  id?: string;
  trip_id?: string;
  estimated_co2_kg?: number;
  transit_mode?: string;
  status?: string;
  payload?: Record<string, unknown>;
}

export interface ExplanationRead {
  id?: string;
  trip_id?: string;
  item_id?: string | null;
  explanation_text?: string;
  source_type?: string;
  created_at?: string;
}

export interface PlaceRead {
  id: string;
  city: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  productive_score?: number;
  crowd_score?: number;
  safety_score?: number;
  cost_per_day?: number;
}

export interface EventRead {
  id: string;
  trip_id: string;
  title: string;
  date: string;
  venue?: string | null;
  payload?: Record<string, unknown>;
}

export interface MemoryRead {
  id: string;
  user_id?: string;
  group_id?: string | null;
  text: string;
  score?: number;
  created_at?: string;
}

export interface ProfileRead {
  id: string;
  user_id: string;
  group_id: string | null;
  travel_pace: string;
  content_interest: number;
  budget_sensitivity: number;
  risk_tolerance: number;
  eco_level: number;
  remote_work: boolean;
  remote_work_mode: boolean;
  work_start: string | null;
  work_end: string | null;
  event_interest: boolean;
}

export interface ScoreRead {
  id?: string;
  place_id?: string;
  crowd_score?: number;
  visual_score?: number;
  safety_score?: number;
  confidence?: number;
}

export type Guide = TravelGuide;
export type ItineraryDay = ItineraryItem;
export type ItineraryActivity = ItineraryItem;
export type CreateActivityRequest = CreateItineraryItemRequest;

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
