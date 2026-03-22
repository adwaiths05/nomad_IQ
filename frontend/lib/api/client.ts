import {
  AuthResponse,
  AuthRequest,
  Trip,
  CreateTripRequest,
  UpdateTripRequest,
  ItineraryItem,
  CreateItineraryItemRequest,
  ChatMessage,
  SendMessageRequest,
  TravelGuide,
  User,
  ApiError,
} from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

class ApiClientClass {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    // Add auth token if available
    const token = this.getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
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
          error.message = errorData.message || errorData.detail || error.message
          error.details = errorData
        } catch {
          // Response was not JSON
        }

        throw error
      }

      if (response.status === 204) {
        return undefined as unknown as T
      }

      return response.json()
    } catch (error) {
      if (error instanceof Object && 'status' in error) {
        throw error as ApiError
      }
      throw {
        status: 500,
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        details: error,
      } as ApiError
    }
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token')
    }
    return null
  }

  private setAuthToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }

  private clearAuthToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  }

  // Auth endpoints
  auth = {
    login: (email: string, password: string): Promise<AuthResponse> =>
      this.request<AuthResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }).then((response) => {
        if (response.access_token) {
          this.setAuthToken(response.access_token)
        }
        return response
      }),

    register: (username: string, email: string, password: string): Promise<AuthResponse> =>
      this.request<AuthResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
      }).then((response) => {
        if (response.access_token) {
          this.setAuthToken(response.access_token)
        }
        return response
      }),

    logout: async (): Promise<void> => {
      try {
        await this.request('/auth/logout', { method: 'POST' })
      } finally {
        this.clearAuthToken()
      }
    },

    getCurrentUser: (): Promise<User> =>
      this.request<User>('/auth/me', { method: 'GET' }),
  }

  // Trip endpoints
  trips = {
    getAll: (): Promise<Trip[]> =>
      this.request<Trip[]>('/trips', { method: 'GET' }),

    getById: (tripId: string): Promise<Trip> =>
      this.request<Trip>(`/trips/${tripId}`, { method: 'GET' }),

    create: (data: CreateTripRequest): Promise<Trip> =>
      this.request<Trip>('/trips', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (tripId: string, data: UpdateTripRequest): Promise<Trip> =>
      this.request<Trip>(`/trips/${tripId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    delete: (tripId: string): Promise<void> =>
      this.request<void>(`/trips/${tripId}`, { method: 'DELETE' }),
  }

  // Itinerary endpoints
  itinerary = {
    getByTrip: (tripId: string): Promise<ItineraryItem[]> =>
      this.request<ItineraryItem[]>(`/trips/${tripId}/itinerary`, {
        method: 'GET',
      }),

    create: (data: CreateItineraryItemRequest): Promise<ItineraryItem> =>
      this.request<ItineraryItem>('/itinerary', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (itemId: string, data: Partial<CreateItineraryItemRequest>): Promise<ItineraryItem> =>
      this.request<ItineraryItem>(`/itinerary/${itemId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    delete: (itemId: string): Promise<void> =>
      this.request<void>(`/itinerary/${itemId}`, { method: 'DELETE' }),
  }

  // Chat endpoints
  chat = {
    getMessages: (tripId: string): Promise<ChatMessage[]> =>
      this.request<ChatMessage[]>(`/trips/${tripId}/chat`, {
        method: 'GET',
      }),

    sendMessage: (tripId: string, message: string): Promise<ChatMessage> =>
      this.request<ChatMessage>(`/trips/${tripId}/chat`, {
        method: 'POST',
        body: JSON.stringify({ message }),
      }),
  }

  // Guide endpoints
  guides = {
    getAll: (): Promise<TravelGuide[]> =>
      this.request<TravelGuide[]>('/guides', { method: 'GET' }),

    getById: (guideId: string): Promise<TravelGuide> =>
      this.request<TravelGuide>(`/guides/${guideId}`, { method: 'GET' }),
  }
}

export const apiClient = new ApiClientClass()
