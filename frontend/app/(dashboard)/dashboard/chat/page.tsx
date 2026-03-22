'use client'

import { useEffect, useState, useRef } from 'react'
import { apiClient } from '@/lib/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader, Send } from 'lucide-react'
import type { ChatMessage } from '@/lib/api/types'

export default function ChatPage() {
  const [trips, setTrips] = useState<any[]>([])
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchTrips()
  }, [])

  useEffect(() => {
    if (selectedTripId) {
      fetchMessages()
    }
  }, [selectedTripId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchTrips = async () => {
    try {
      setLoading(true)
      const data = await apiClient.trips.getAll()
      setTrips(data)
      if (data.length > 0) {
        setSelectedTripId(data[0].trip_id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trips')
    } finally {
      setLoading(false)
    }
  }

  const fetchMessages = async () => {
    if (!selectedTripId) return

    try {
      const data = await apiClient.chat.getMessages(selectedTripId)
      setMessages(data)
    } catch (err) {
      console.log('[v0] Error fetching messages:', err)
      setMessages([])
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !selectedTripId || sending) return

    const userMessage = input.trim()
    setInput('')
    setSending(true)

    try {
      // Add user message to UI
      const userMsg: ChatMessage = {
        message_id: Date.now().toString(),
        trip_id: selectedTripId,
        sender: 'user',
        message: userMessage,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMsg])

      // Send to backend
      const response = await apiClient.chat.sendMessage(selectedTripId, userMessage)

      // Add AI response
      setMessages((prev) => [...prev, response])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <Loader className="w-6 h-6 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="p-8 flex flex-col h-screen">
      <h1 className="text-3xl font-bold text-slate-900 mb-8">AI Travel Assistant</h1>

      {/* Trip Selector */}
      {trips.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-sm">Select Trip</CardTitle>
          </CardHeader>
          <CardContent>
            <select
              value={selectedTripId || ''}
              onChange={(e) => {
                setSelectedTripId(e.target.value)
                setMessages([])
              }}
              className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm"
            >
              {trips.map((trip) => (
                <option key={trip.trip_id} value={trip.trip_id}>
                  {trip.destination} ({new Date(trip.start_date).toLocaleDateString()})
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      )}

      {/* Messages Container */}
      <Card className="flex-1 mb-6 overflow-hidden flex flex-col">
        <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center text-slate-500 text-center">
              <div>
                <p className="text-lg font-semibold mb-2">Start your conversation</p>
                <p className="text-sm">Ask the AI assistant for travel recommendations, itinerary suggestions, or any travel advice!</p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.message_id}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  msg.sender === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-slate-100 text-slate-900 rounded-bl-none'
                }`}
              >
                <p className="text-sm">{msg.message}</p>
                <p className={`text-xs mt-1 ${msg.sender === 'user' ? 'text-blue-100' : 'text-slate-500'}`}>
                  {new Date(msg.created_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          ))}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>
      </Card>

      {/* Input Form */}
      <form onSubmit={handleSendMessage} className="flex gap-2">
        <Input
          placeholder="Ask me anything about your trip..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending || !selectedTripId}
          className="flex-1"
        />
        <Button
          type="submit"
          disabled={sending || !input.trim() || !selectedTripId}
          className="bg-blue-600 hover:bg-blue-700"
        >
          {sending ? (
            <Loader className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </form>
    </div>
  )
}
