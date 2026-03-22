'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader, Trash2, Eye } from 'lucide-react'
import type { Trip } from '@/lib/api/types'

export default function TripsPage() {
  const router = useRouter()
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchTrips()
  }, [])

  const fetchTrips = async () => {
    try {
      setLoading(true)
      const data = await apiClient.trips.getAll()
      setTrips(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trips')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (tripId: string) => {
    if (!confirm('Are you sure you want to delete this trip?')) return

    try {
      await apiClient.trips.delete(tripId)
      setTrips(trips.filter((t) => t.trip_id !== tripId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete trip')
    }
  }

  const filteredTrips = trips.filter(
    (trip) =>
      trip.destination.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trip.theme.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">My Trips</h1>
          <p className="text-slate-600 mt-1">Manage and view all your trips</p>
        </div>
        <Link href="/dashboard/trips/new">
          <Button className="bg-blue-600 hover:bg-blue-700">Create New Trip</Button>
        </Link>
      </div>

      {/* Search */}
      <div className="mb-6">
        <Input
          placeholder="Search trips by destination or theme..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-md"
        />
      </div>

      {/* Content */}
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
      ) : filteredTrips.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <p className="text-slate-600 mb-4">
              {searchTerm ? 'No trips match your search.' : 'No trips yet. Create your first trip!'}
            </p>
            {!searchTerm && (
              <Link href="/dashboard/trips/new">
                <Button className="bg-blue-600 hover:bg-blue-700">Create First Trip</Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-100 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">Destination</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">Theme</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">Dates</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">Budget</th>
                <th className="px-6 py-3 text-right text-sm font-semibold text-slate-900">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredTrips.map((trip) => (
                <tr key={trip.trip_id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 text-slate-900 font-medium">{trip.destination}</td>
                  <td className="px-6 py-4 text-slate-600">{trip.theme}</td>
                  <td className="px-6 py-4 text-slate-600">
                    {new Date(trip.start_date).toLocaleDateString()} -{' '}
                    {new Date(trip.end_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-slate-600">
                    ${trip.budget ? trip.budget.toLocaleString() : 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <Link href={`/dashboard/trips/${trip.trip_id}`}>
                      <Button size="sm" variant="outline" className="gap-1">
                        <Eye className="w-4 h-4" />
                        View
                      </Button>
                    </Link>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:bg-red-50 gap-1"
                      onClick={() => handleDelete(trip.trip_id)}
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
