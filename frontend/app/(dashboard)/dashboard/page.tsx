'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/context/auth-context'
import { apiClient } from '@/lib/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Loader } from 'lucide-react'
import type { Trip } from '@/lib/api/types'

export default function DashboardPage() {
  const { user } = useAuth()
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTrips = async () => {
      try {
        const data = await apiClient.trips.getAll()
        setTrips(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch trips')
      } finally {
        setLoading(false)
      }
    }

    fetchTrips()
  }, [])

  const upcomingTrips = trips.filter((trip) => new Date(trip.start_date) > new Date())
  const pastTrips = trips.filter((trip) => new Date(trip.start_date) <= new Date())

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">
          Welcome back, {user?.username || 'Traveler'}!
        </h1>
        <p className="text-slate-600">Manage your trips and plan your next adventure</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">Total Trips</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{trips.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">Upcoming Trips</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{upcomingTrips.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">Completed Trips</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{pastTrips.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/dashboard/trips/new">
            <Button className="w-full bg-blue-600 hover:bg-blue-700 py-6">
              Create New Trip
            </Button>
          </Link>
          <Link href="/dashboard/chat">
            <Button variant="outline" className="w-full py-6">
              Ask AI Assistant
            </Button>
          </Link>
        </div>
      </div>

      {/* Trips Section */}
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
      ) : (
        <>
          {/* Upcoming Trips */}
          {upcomingTrips.length > 0 && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-slate-900 mb-4">Upcoming Trips</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {upcomingTrips.map((trip) => (
                  <Link key={trip.trip_id} href={`/dashboard/trips/${trip.trip_id}`}>
                    <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                      <CardHeader>
                        <CardTitle className="text-lg">{trip.destination}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div>
                            <p className="text-sm text-slate-600">Dates</p>
                            <p className="text-slate-900">
                              {new Date(trip.start_date).toLocaleDateString()} -{' '}
                              {new Date(trip.end_date).toLocaleDateString()}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-slate-600">Theme</p>
                            <p className="text-slate-900">{trip.theme}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Past Trips */}
          {pastTrips.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4">Past Trips</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {pastTrips.map((trip) => (
                  <Link key={trip.trip_id} href={`/dashboard/trips/${trip.trip_id}`}>
                    <Card className="hover:shadow-lg transition-shadow cursor-pointer opacity-75">
                      <CardHeader>
                        <CardTitle className="text-lg">{trip.destination}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div>
                            <p className="text-sm text-slate-600">Dates</p>
                            <p className="text-slate-900">
                              {new Date(trip.start_date).toLocaleDateString()} -{' '}
                              {new Date(trip.end_date).toLocaleDateString()}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-slate-600">Theme</p>
                            <p className="text-slate-900">{trip.theme}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {trips.length === 0 && (
            <Card className="text-center py-12">
              <CardContent>
                <p className="text-slate-600 mb-4">No trips yet. Start by creating your first trip!</p>
                <Link href="/dashboard/trips/new">
                  <Button className="bg-blue-600 hover:bg-blue-700">Create First Trip</Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
