import {
  ApiError,
  AuthResponse,
  AmbientAssistRequest,
  AmbientAssistResponse,
  BudgetRead,
  ChatMessage,
  CreateItineraryItemRequest,
  CreateTripRequest,
  EnvironmentRead,
  EventRead,
  ExplanationRead,
  ItineraryItem,
  MemoryRead,
  PlaceRead,
  ProfileRead,
  ScoreRead,
  QueryExpansionResponse,
  TravelGuide,
  Trip,
  UpdateItineraryItemRequest,
  UpdateTripRequest,
  User,
  WeatherRead,
} from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

class ApiClientClass {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('auth_token')
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('refresh_token')
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem('auth_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }

  private clearTokens(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
  }

  private setCurrentUserId(userId: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem('current_user_id', userId)
  }

  private getCurrentUserId(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('current_user_id')
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = new Headers(options.headers)
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }

    const token = this.getAuthToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const error: ApiError = {
          status: response.status,
          message: response.statusText,
        }

        try {
          const errorData = await response.json()
          error.message = String(errorData.detail || errorData.message || error.message)
          error.details = errorData as Record<string, unknown>
        } catch {
          // Ignore JSON parse errors for non-JSON responses.
        }

        throw error
      }

      if (response.status === 204) {
        return undefined as T
      }

      return (await response.json()) as T
    } catch (error) {
      if (error && typeof error === 'object' && 'status' in error) {
        throw error
      }
      throw {
        status: 500,
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        details: { cause: error },
      } as ApiError
    }
  }

  private normalizeUser(raw: Record<string, unknown>): User {
    const id = String(raw.id || '')
    const name = String(raw.name || raw.username || 'Traveler')
    const email = String(raw.email || '')
    const createdAt = String(raw.created_at || new Date().toISOString())

    return {
      id,
      name,
      username: name,
      email,
      created_at: createdAt,
    }
  }

  private normalizeTrip(raw: Record<string, unknown>): Trip {
    const id = String(raw.id || raw.trip_id || '')
    const city = String(raw.city || raw.destination || '')
    const budgetMin = Number(raw.budget_min ?? raw.budget ?? 0)
    const budgetMax = Number(raw.budget_max ?? raw.budget ?? 0)
    const budget =
      raw.budget !== undefined && raw.budget !== null
        ? Number(raw.budget)
        : budgetMin > 0 || budgetMax > 0
          ? Math.round((budgetMin + budgetMax) / 2)
          : null

    return {
      id,
      trip_id: id,
      user_id: String(raw.user_id || this.getCurrentUserId() || ''),
      group_id: (raw.group_id as string | null) ?? null,
      city,
      destination: city,
      start_date: String(raw.start_date || ''),
      end_date: String(raw.end_date || ''),
      budget_min: Number.isFinite(budgetMin) ? budgetMin : 0,
      budget_max: Number.isFinite(budgetMax) ? budgetMax : 0,
      budget,
      flexibility_level: String(raw.flexibility_level || raw.theme || 'moderate'),
      theme: String(raw.theme || raw.flexibility_level || 'moderate'),
      status: String(raw.status || 'draft'),
      description: (raw.description as string | null) ?? null,
      created_at: String(raw.created_at || raw.start_date || new Date().toISOString()),
      updated_at: String(raw.updated_at || raw.end_date || new Date().toISOString()),
    }
  }

  private normalizeItineraryItem(
    raw: Record<string, unknown>,
    dayLookup: Record<string, number>,
    tripId: string
  ): ItineraryItem {
    const id = String(raw.id || raw.item_id || '')
    const dayId = String(raw.day_id || '')
    const activity = String(raw.activity_type || raw.activity || 'Activity')

    return {
      id,
      item_id: id,
      trip_id: tripId,
      day_id: dayId,
      day: dayLookup[dayId] || Number(raw.day || 1),
      place_id: (raw.place_id as string | null) ?? null,
      start_time: raw.start_time ? String(raw.start_time) : null,
      end_time: raw.end_time ? String(raw.end_time) : null,
      activity_type: activity,
      activity,
      location: String(raw.location || raw.source_type || 'Unknown'),
      travel_time_minutes: Number(raw.travel_time_minutes ?? 0),
      cost_estimate: Number(raw.cost_estimate ?? 0),
      confidence_score: String(raw.confidence_score || 'medium'),
      source_type: String(raw.source_type || 'system'),
      notes: (raw.notes as string | null) ?? null,
      created_at: String(raw.created_at || new Date().toISOString()),
      updated_at: String(raw.updated_at || new Date().toISOString()),
    }
  }

  auth = {
    login: async (email: string, password: string): Promise<AuthResponse> => {
      const tokens = await this.request<{ access_token: string; refresh_token: string; token_type?: string }>(
        '/auth/login',
        {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        }
      )

      this.setTokens(tokens.access_token, tokens.refresh_token)

      const me = await this.request<Record<string, unknown>>('/auth/me', { method: 'GET' })
      const user = this.normalizeUser(me)
      this.setCurrentUserId(user.id)

      return {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        token_type: tokens.token_type || 'bearer',
        user,
      }
    },

    register: async (username: string, email: string, password: string): Promise<AuthResponse> => {
      const userRaw = await this.request<Record<string, unknown>>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ name: username, email, password }),
      })

      const user = this.normalizeUser(userRaw)
      this.setCurrentUserId(user.id)

      const tokens = await this.request<{ access_token: string; refresh_token: string; token_type?: string }>(
        '/auth/login',
        {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        }
      )

      this.setTokens(tokens.access_token, tokens.refresh_token)

      return {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        token_type: tokens.token_type || 'bearer',
        user,
      }
    },

    refresh: async (): Promise<{ access_token: string; refresh_token: string; token_type?: string }> => {
      const refreshToken = this.getRefreshToken()
      if (!refreshToken) {
        throw { status: 401, message: 'No refresh token available' } as ApiError
      }

      const tokens = await this.request<{ access_token: string; refresh_token: string; token_type?: string }>(
        '/auth/refresh',
        {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        }
      )
      this.setTokens(tokens.access_token, tokens.refresh_token)
      return tokens
    },

    logout: async (): Promise<void> => {
      const refreshToken = this.getRefreshToken()
      try {
        if (refreshToken) {
          await this.request('/auth/logout', {
            method: 'POST',
            body: JSON.stringify({ refresh_token: refreshToken }),
          })
        }
      } finally {
        this.clearTokens()
      }
    },

    getCurrentUser: async (): Promise<User> => {
      const me = await this.request<Record<string, unknown>>('/auth/me', { method: 'GET' })
      const user = this.normalizeUser(me)
      this.setCurrentUserId(user.id)
      return user
    },
  }

  trips = {
    getAll: async (): Promise<Trip[]> => {
      const rows = await this.request<Record<string, unknown>[]>('/trips', { method: 'GET' })
      return rows.map((row) => this.normalizeTrip(row))
    },

    getById: async (tripId: string): Promise<Trip> => {
      const row = await this.request<Record<string, unknown>>(`/trips/${tripId}`, { method: 'GET' })
      return this.normalizeTrip(row)
    },

    create: async (data: CreateTripRequest): Promise<Trip> => {
      const city = data.city || data.destination || 'Unknown city'
      const userId = data.user_id || this.getCurrentUserId()
      if (!userId) {
        throw { status: 400, message: 'Missing user id for trip creation' } as ApiError
      }

      const budgetFromSingle = data.budget ?? null
      const budgetMin = data.budget_min ?? (budgetFromSingle != null ? Math.max(0, Math.floor(budgetFromSingle * 0.8)) : 500)
      const budgetMax = data.budget_max ?? (budgetFromSingle != null ? Math.max(budgetMin + 1, Math.ceil(budgetFromSingle * 1.2)) : 1500)

      const payload = {
        user_id: userId,
        group_id: data.group_id ?? null,
        city,
        start_date: data.start_date,
        end_date: data.end_date,
        budget_min: budgetMin,
        budget_max: budgetMax,
        flexibility_level: data.flexibility_level || data.theme || 'moderate',
      }

      const row = await this.request<Record<string, unknown>>('/trips', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      return this.normalizeTrip(row)
    },

    update: async (tripId: string, data: UpdateTripRequest): Promise<Trip> => {
      const payload: Record<string, unknown> = {}
      if (data.city || data.destination) payload.city = data.city || data.destination
      if (data.start_date) payload.start_date = data.start_date
      if (data.end_date) payload.end_date = data.end_date
      if (data.budget_min != null) payload.budget_min = data.budget_min
      if (data.budget_max != null) payload.budget_max = data.budget_max
      if (data.budget != null) {
        payload.budget_min = Math.max(0, Math.floor(data.budget * 0.8))
        payload.budget_max = Math.max(Number(payload.budget_min) + 1, Math.ceil(data.budget * 1.2))
      }
      if (data.flexibility_level || data.theme) payload.flexibility_level = data.flexibility_level || data.theme
      if (data.status) payload.status = data.status

      const row = await this.request<Record<string, unknown>>(`/trips/${tripId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      })

      return this.normalizeTrip(row)
    },

    delete: async (tripId: string): Promise<void> => {
      // Backend has no delete endpoint; archive via status patch.
      await this.trips.update(tripId, { status: 'archived' })
    },
  }

  itinerary = {
    getByTrip: async (tripId: string): Promise<ItineraryItem[]> => {
      const payload = await this.request<{ days?: Array<{ id: string; day_number: number }>; items?: Record<string, unknown>[] }>(
        `/trips/${tripId}/itinerary`,
        { method: 'GET' }
      )

      const days = payload.days || []
      const dayLookup = days.reduce((acc, day) => {
        acc[String(day.id)] = Number(day.day_number)
        return acc
      }, {} as Record<string, number>)

      const items = payload.items || []
      return items.map((row) => this.normalizeItineraryItem(row, dayLookup, tripId))
    },

    create: async (_data: CreateItineraryItemRequest): Promise<ItineraryItem> => {
      throw {
        status: 501,
        message: 'Backend does not expose create-itinerary-item endpoint. Use /plan-trip or /itinerary/optimize.',
      } as ApiError
    },

    update: async (itemId: string, data: UpdateItineraryItemRequest): Promise<ItineraryItem> => {
      const row = await this.request<Record<string, unknown>>(`/itinerary/items/${itemId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      })
      return this.normalizeItineraryItem(row, {}, '')
    },

    delete: async (_itemId: string): Promise<void> => {
      throw {
        status: 501,
        message: 'Backend does not expose delete-itinerary-item endpoint.',
      } as ApiError
    },

    optimize: async (payload: {
      trip_id: string
      flexibility_level?: 'strict' | 'moderate' | 'light' | string
      remote_work_mode?: boolean
      work_start?: string | null
      work_end?: string | null
      latitude?: number
      longitude?: number
    }): Promise<{ trip_id: string; optimized_items: Record<string, unknown>[] }> =>
      this.request<{ trip_id: string; optimized_items: Record<string, unknown>[] }>('/itinerary/optimize', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  }

  budget = {
    estimate: (tripId: string): Promise<BudgetRead> =>
      this.request<BudgetRead>('/budget/estimate', {
        method: 'POST',
        body: JSON.stringify({ trip_id: tripId }),
      }),

    update: (tripId: string, actualSpent: number): Promise<BudgetRead> =>
      this.request<BudgetRead>('/budget/update', {
        method: 'POST',
        body: JSON.stringify({ trip_id: tripId, actual_spent: actualSpent }),
      }),

    optimize: (tripId: string): Promise<BudgetRead> =>
      this.request<BudgetRead>('/budget/optimize', {
        method: 'POST',
        body: JSON.stringify({ trip_id: tripId }),
      }),

    getByTrip: (tripId: string): Promise<BudgetRead> =>
      this.request<BudgetRead>(`/trips/${tripId}/budget`, { method: 'GET' }),
  }

  weather = {
    check: (city: string, date: string): Promise<WeatherRead> =>
      this.request<WeatherRead>('/weather/check', {
        method: 'POST',
        body: JSON.stringify({ city, date }),
      }),
  }

  environment = {
    evaluate: (tripId: string, routeDistanceKm: number, transitMode: string): Promise<EnvironmentRead> =>
      this.request<EnvironmentRead>('/environment/evaluate', {
        method: 'POST',
        body: JSON.stringify({ trip_id: tripId, route_distance_km: routeDistanceKm, transit_mode: transitMode }),
      }),

    getByTrip: (tripId: string): Promise<EnvironmentRead> =>
      this.request<EnvironmentRead>(`/trips/${tripId}/environment`, { method: 'GET' }),
  }

  explain = {
    getByTrip: (tripId: string): Promise<ExplanationRead[]> =>
      this.request<ExplanationRead[]>(`/trips/${tripId}/explanations`, { method: 'GET' }),

    getByItem: (itemId: string): Promise<ExplanationRead> =>
      this.request<ExplanationRead>(`/itinerary/items/${itemId}/explanation`, { method: 'GET' }),
  }

  places = {
    getAll: (): Promise<PlaceRead[]> => this.request<PlaceRead[]>('/places', { method: 'GET' }),

    getById: (placeId: string): Promise<PlaceRead> => this.request<PlaceRead>(`/places/${placeId}`, { method: 'GET' }),

    search: (payload: { city: string; category?: string | null; productive_only?: boolean }): Promise<PlaceRead[]> =>
      this.request<PlaceRead[]>('/places/search', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  }

  events = {
    getAll: (): Promise<EventRead[]> => this.request<EventRead[]>('/events', { method: 'GET' }),

    syncByTrip: (tripId: string): Promise<EventRead[]> =>
      this.request<EventRead[]>(`/events/sync/${tripId}`, { method: 'POST' }),

    getById: (eventId: string): Promise<EventRead> => this.request<EventRead>(`/events/${eventId}`, { method: 'GET' }),
  }

  memory = {
    create: (payload: { user_id?: string; group_id?: string | null; content: string; metadata?: Record<string, unknown> }): Promise<MemoryRead> =>
      this.request<MemoryRead>('/memory', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    search: (payload: { query: string; user_id?: string; group_id?: string | null; limit?: number }): Promise<MemoryRead[]> =>
      this.request<MemoryRead[]>('/memory/search', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    searchTool: (payload: { query: string; user_id?: string; group_id?: string | null; limit?: number }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/memory/search-tool', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  }

  profiles = {
    create: (payload: Record<string, unknown>): Promise<ProfileRead> =>
      this.request<ProfileRead>('/profiles', { method: 'POST', body: JSON.stringify(payload) }),

    update: (profileId: string, payload: Record<string, unknown>): Promise<ProfileRead> =>
      this.request<ProfileRead>(`/profiles/${profileId}`, { method: 'PUT', body: JSON.stringify(payload) }),

    getById: (profileId: string): Promise<ProfileRead> =>
      this.request<ProfileRead>(`/profiles/${profileId}`, { method: 'GET' }),
  }

  scoring = {
    scorePlace: (placeId: string): Promise<ScoreRead> =>
      this.request<ScoreRead>('/score/place', {
        method: 'POST',
        body: JSON.stringify({ place_id: placeId }),
      }),

    scoreBatch: (placeIds: string[]): Promise<ScoreRead[]> =>
      this.request<ScoreRead[]>('/score/batch', {
        method: 'POST',
        body: JSON.stringify({ place_ids: placeIds }),
      }),
  }

  integrations = {
    transportSearchTrains: (payload: {
      origin_city: string
      destination_city: string
      journey_date?: string | null
      limit?: number
    }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/transport/search-trains', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    transportSearchBuses: (payload: {
      origin_city: string
      destination_city: string
      journey_date?: string | null
      limit?: number
    }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/transport/search-buses', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    transportSearchMetro: (payload: {
      origin_lat: number
      origin_lng: number
      destination_lat: number
      destination_lng: number
      city?: string | null
      limit?: number
    }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/transport/search-metro', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    mapsCitySpots: (city: string, maxResults = 10): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/maps/city-spots', {
        method: 'POST',
        body: JSON.stringify({ city, max_results: maxResults }),
      }),

    mapsNearbySpots: (payload: {
      latitude: number
      longitude: number
      radius_meters?: number
      max_results?: number
    }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/maps/nearby-spots', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    mapsTransitDuration: (payload: {
      origin_lat: number
      origin_lng: number
      destination_lat: number
      destination_lng: number
      mode?: string
    }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/maps/transit-duration', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    eventsSearch: (payload: {
      city: string
      start_date: string
      end_date: string
      limit?: number
    }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/events/search', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    eventsSearchLocal: (payload: {
      city: string
      start_date: string
      end_date: string
      limit?: number
    }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/events/search-local', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    eventsDiscover: (payload: {
      city: string
      start_date: string
      end_date: string
      latitude?: number
      longitude?: number
      budget_cap?: number
      time_of_day?: string
      location_type?: string
      max_results?: number
    }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/events/discover', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    weatherFiveDayForecast: (city: string): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/weather/five-day-forecast', {
        method: 'POST',
        body: JSON.stringify({ city }),
      }),

    financeCostBaseline: (city: string): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/finance/cost-baseline', {
        method: 'POST',
        body: JSON.stringify({ city }),
      }),

    safetyScore: (
      latitude: number,
      longitude: number,
      options?: {
        city?: string
        event_count?: number
        time_of_day?: string
        location_type?: string
      }
    ): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/safety/score', {
        method: 'POST',
        body: JSON.stringify({ latitude, longitude, ...(options || {}) }),
      }),

    environmentRouteEmissions: (distanceKm: number, mode = 'passenger_train'): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/environment/route-emissions', {
        method: 'POST',
        body: JSON.stringify({ distance_km: distanceKm, mode }),
      }),

    ragSearchLongTerm: (query: string, limit = 5): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/rag/search-long-term', {
        method: 'POST',
        body: JSON.stringify({ query, limit }),
      }),

    ragSearchShortTerm: (query: string, limit = 5): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/rag/search-short-term', {
        method: 'POST',
        body: JSON.stringify({ query, limit }),
      }),

    ragStore: (payload: { content: string; memory_type?: string; metadata?: Record<string, unknown> }): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/integrations/rag/store', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  }

  system = {
    planTrip: (tripId: string): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>('/plan-trip', {
        method: 'POST',
        body: JSON.stringify({ trip_id: tripId }),
      }),

    replanTrip: (tripId: string, reason: string): Promise<Record<string, unknown>> =>
      this.request<Record<string, unknown>>(`/trips/${tripId}/replan`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
  }

  // Existing compatibility namespaces.
  chat = {
    getMessages: (_tripId: string): Promise<ChatMessage[]> => Promise.resolve([]),
    sendMessage: (_tripId: string, _message: string): Promise<ChatMessage> =>
      Promise.resolve({
        message_id: crypto.randomUUID(),
        trip_id: _tripId,
        sender: 'ai',
        message: 'Chat endpoint is not exposed by the backend yet.',
        created_at: new Date().toISOString(),
      }),
  }

  ambientAi = {
    expand: (payload: AmbientAssistRequest): Promise<QueryExpansionResponse> =>
      this.request<QueryExpansionResponse>('/ai/expand', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    assist: (payload: AmbientAssistRequest): Promise<AmbientAssistResponse> =>
      this.request<AmbientAssistResponse>('/ai/assist', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  }

  guides = {
    getAll: (): Promise<TravelGuide[]> => Promise.resolve([]),
    getById: (_guideId: string): Promise<TravelGuide> =>
      Promise.reject({ status: 404, message: 'Guide endpoint not available' } as ApiError),
  }
}

export const apiClient = new ApiClientClass()
