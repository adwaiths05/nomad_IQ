'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader, Edit2, Trash2, ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import type { Trip } from '@/lib/api/types'

export default function TripDetailPage() {
  const params = useParams()
  const router = useRouter()
  const tripId = params.tripId as string

  const [trip, setTrip] = useState<Trip | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTrip = async () => {
      try {
        const data = await apiClient.trips.getById(tripId)
        setTrip(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch trip')
      } finally {
        setLoading(false)
      }
    }

    fetchTrip()
  }, [tripId])

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this trip?')) return

    try {
      await apiClient.trips.delete(tripId)
      router.push('/dashboard/trips')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete trip')
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <Loader className="w-6 h-6 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error || !trip) {
    return (
      <div className="p-8">
        <Link href="/dashboard/trips">
          <Button variant="outline" className="gap-2 mb-8">
            <ArrowLeft className="w-4 h-4" />
            Back to Trips
          </Button>
        </Link>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error || 'Trip not found'}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const duration = Math.ceil(
    (new Date(trip.end_date).getTime() - new Date(trip.start_date).getTime()) / (1000 * 60 * 60 * 24)
  )

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <Link href="/dashboard/trips">
          <Button variant="outline" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Trips
          </Button>
        </Link>
        <div className="flex gap-2">
          <Link href={`/dashboard/trips/${tripId}/edit`}>
            <Button variant="outline" className="gap-2">
              <Edit2 className="w-4 h-4" />
              Edit
            </Button>
          </Link>
          <Button variant="outline" className="text-red-600 hover:bg-red-50 gap-2" onClick={handleDelete}>
            <Trash2 className="w-4 h-4" />
            Delete
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trip Overview */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-3xl">{trip.destination}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-slate-600 mb-1">Duration</p>
                  <p className="text-xl font-semibold text-slate-900">{duration} days</p>
                </div>
                <div>
                  <p className="text-sm text-slate-600 mb-1">Theme</p>
                  <p className="text-xl font-semibold text-slate-900">{trip.theme}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-600 mb-1">Start Date</p>
                  <p className="text-lg font-semibold text-slate-900">
                    {new Date(trip.start_date).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-600 mb-1">End Date</p>
                  <p className="text-lg font-semibold text-slate-900">
                    {new Date(trip.end_date).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {trip.budget && (
                <div className="pt-4 border-t border-slate-200">
                  <p className="text-sm text-slate-600 mb-1">Budget</p>
                  <p className="text-2xl font-bold text-blue-600">${trip.budget.toLocaleString()}</p>
                </div>
              )}

              {trip.description && (
                <div className="pt-4 border-t border-slate-200">
                  <p className="text-sm text-slate-600 mb-2">Description</p>
                  <p className="text-slate-700 whitespace-pre-wrap">{trip.description}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Trip Actions</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <Link href={`/dashboard/itinerary?tripId=${tripId}`}>
                <Button variant="outline" className="w-full">
                  View Itinerary
                </Button>
              </Link>
              <Link href="/dashboard/chat">
                <Button variant="outline" className="w-full">
                  Get AI Recommendations
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Trip Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-slate-600 mb-1">Trip ID</p>
                <p className="text-sm font-mono text-slate-900 break-all">{trip.trip_id}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600 mb-1">Created</p>
                <p className="text-sm text-slate-900">
                  {new Date(trip.created_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-600 mb-1">Last Updated</p>
                <p className="text-sm text-slate-900">
                  {new Date(trip.updated_at).toLocaleDateString()}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
