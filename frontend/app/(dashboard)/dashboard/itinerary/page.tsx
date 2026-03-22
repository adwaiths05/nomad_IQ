'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader, Plus, Trash2, Edit2 } from 'lucide-react'
import type { Trip, ItineraryItem } from '@/lib/api/types'

export default function ItineraryPage() {
  const searchParams = useSearchParams()
  const tripId = searchParams.get('tripId')

  const [trips, setTrips] = useState<Trip[]>([])
  const [selectedTripId, setSelectedTripId] = useState<string | null>(tripId || null)
  const [itineraryItems, setItineraryItems] = useState<ItineraryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    day: '',
    activity: '',
    location: '',
    startTime: '',
    endTime: '',
    notes: '',
  })

  useEffect(() => {
    fetchTrips()
  }, [])

  useEffect(() => {
    if (selectedTripId) {
      fetchItinerary()
    }
  }, [selectedTripId])

  const fetchTrips = async () => {
    try {
      setLoading(true)
      const data = await apiClient.trips.getAll()
      setTrips(data)
      if (!selectedTripId && data.length > 0) {
        setSelectedTripId(data[0].trip_id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trips')
    } finally {
      setLoading(false)
    }
  }

  const fetchItinerary = async () => {
    if (!selectedTripId) return

    try {
      const data = await apiClient.itinerary.getByTrip(selectedTripId)
      setItineraryItems(data)
    } catch (err) {
      console.log('[v0] Error fetching itinerary:', err)
      setItineraryItems([])
    }
  }

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTripId) return

    setError('Creating itinerary items directly is not exposed by backend. Use planner (/plan) and optimize endpoints.')
  }

  const handleDeleteItem = async (itemId: string) => {
    if (!confirm('Are you sure you want to delete this item?')) return
    void itemId
    setError('Deleting itinerary items directly is not exposed by backend.')
  }

  const selectedTrip = trips.find((t) => t.trip_id === selectedTripId)
  const groupedByDay = itineraryItems.reduce(
    (acc, item) => {
      if (!acc[item.day]) acc[item.day] = []
      acc[item.day].push(item)
      return acc
    },
    {} as Record<number, ItineraryItem[]>
  )

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-slate-900 mb-8">Trip Itinerary</h1>

      {/* Trip Selector */}
      {trips.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Select Trip</CardTitle>
          </CardHeader>
          <CardContent>
            <select
              value={selectedTripId || ''}
              onChange={(e) => setSelectedTripId(e.target.value)}
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

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      ) : error ? (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      ) : !selectedTripId ? (
        <Card className="text-center py-12">
          <CardContent>
            <p className="text-slate-600">No trips available. Create a trip first.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Add Item Button */}
          {!showForm && (
            <Button onClick={() => setShowForm(true)} className="bg-blue-600 hover:bg-blue-700 gap-2">
              <Plus className="w-4 h-4" />
              Add Activity
            </Button>
          )}

          {/* Form */}
          {showForm && (
            <Card>
              <CardHeader>
                <CardTitle>Add New Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAddItem} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Day *</label>
                      <Input
                        type="number"
                        min="1"
                        placeholder="1"
                        value={formData.day}
                        onChange={(e) => setFormData({ ...formData, day: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Activity *</label>
                      <Input
                        placeholder="e.g., Visit Temple"
                        value={formData.activity}
                        onChange={(e) => setFormData({ ...formData, activity: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Location *</label>
                      <Input
                        placeholder="e.g., Tokyo"
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Start Time</label>
                      <Input
                        type="time"
                        value={formData.startTime}
                        onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">End Time</label>
                      <Input
                        type="time"
                        value={formData.endTime}
                        onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Notes</label>
                    <textarea
                      placeholder="Add any notes..."
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                      Add Activity
                    </Button>
                    <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Itinerary Items */}
          {Object.keys(groupedByDay).length === 0 ? (
            <Card className="text-center py-12">
              <CardContent>
                <p className="text-slate-600">No activities yet. Add your first activity!</p>
              </CardContent>
            </Card>
          ) : (
            Object.entries(groupedByDay)
              .sort(([dayA], [dayB]) => parseInt(dayA) - parseInt(dayB))
              .map(([day, items]) => (
                <div key={day}>
                  <h3 className="text-lg font-bold text-slate-900 mb-3">Day {day}</h3>
                  <div className="space-y-3">
                    {items.map((item) => (
                      <Card key={item.item_id} className="hover:shadow-md transition-shadow">
                        <CardContent className="pt-6">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <h4 className="text-lg font-semibold text-slate-900">{item.activity}</h4>
                              <p className="text-slate-600">{item.location}</p>
                              {(item.start_time || item.end_time) && (
                                <p className="text-sm text-slate-500 mt-1">
                                  {item.start_time && new Date(`2000-01-01T${item.start_time}`).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                  {item.start_time && item.end_time && ' - '}
                                  {item.end_time && new Date(`2000-01-01T${item.end_time}`).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </p>
                              )}
                              {item.notes && <p className="text-slate-700 text-sm mt-2">{item.notes}</p>}
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 hover:bg-red-50 gap-1 ml-2"
                              onClick={() => handleDeleteItem(item.item_id)}
                            >
                              <Trash2 className="w-4 h-4" />
                              Delete
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ))
          )}
        </div>
      )}
    </div>
  )
}
