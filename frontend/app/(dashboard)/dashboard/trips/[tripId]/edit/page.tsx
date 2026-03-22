'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'
import { AlertCircle, ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import type { Trip } from '@/lib/api/types'

const THEMES = ['Adventure', 'Beach', 'Cultural', 'Food', 'Hiking', 'Luxury', 'Budget', 'Family', 'Solo', 'Romantic']

export default function EditTripPage() {
  const params = useParams()
  const router = useRouter()
  const tripId = params.tripId as string

  const [trip, setTrip] = useState<Trip | null>(null)
  const [formData, setFormData] = useState({
    destination: '',
    startDate: '',
    endDate: '',
    theme: '',
    budget: '',
    description: '',
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    const fetchTrip = async () => {
      try {
        const data = await apiClient.trips.getById(tripId)
        setTrip(data)
        setFormData({
          destination: data.destination,
          startDate: data.start_date.split('T')[0],
          endDate: data.end_date.split('T')[0],
          theme: data.theme,
          budget: data.budget?.toString() || '',
          description: data.description || '',
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch trip')
      } finally {
        setIsLoading(false)
      }
    }

    fetchTrip()
  }, [tripId])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!formData.destination || !formData.startDate || !formData.endDate || !formData.theme) {
      setError('Please fill in all required fields')
      return
    }

    if (new Date(formData.startDate) >= new Date(formData.endDate)) {
      setError('End date must be after start date')
      return
    }

    setIsSaving(true)

    try {
      await apiClient.trips.update(tripId, {
        destination: formData.destination,
        start_date: formData.startDate,
        end_date: formData.endDate,
        theme: formData.theme,
        budget: formData.budget ? parseInt(formData.budget) : null,
        description: formData.description || null,
      })

      router.push(`/dashboard/trips/${tripId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update trip')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <Spinner className="w-6 h-6" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <Link href={`/dashboard/trips/${tripId}`}>
        <Button variant="outline" className="gap-2 mb-8">
          <ArrowLeft className="w-4 h-4" />
          Back to Trip
        </Button>
      </Link>

      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Edit Trip</h1>
        <p className="text-slate-600 mb-8">Update your trip details</p>

        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label htmlFor="destination" className="text-sm font-medium">
                    Destination *
                  </label>
                  <Input
                    id="destination"
                    name="destination"
                    placeholder="e.g., Tokyo, Japan"
                    value={formData.destination}
                    onChange={handleChange}
                    disabled={isSaving}
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="theme" className="text-sm font-medium">
                    Trip Theme *
                  </label>
                  <select
                    id="theme"
                    name="theme"
                    value={formData.theme}
                    onChange={handleChange}
                    disabled={isSaving}
                    className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm"
                  >
                    <option value="">Select a theme</option>
                    {THEMES.map((theme) => (
                      <option key={theme} value={theme}>
                        {theme}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="startDate" className="text-sm font-medium">
                    Start Date *
                  </label>
                  <Input
                    id="startDate"
                    name="startDate"
                    type="date"
                    value={formData.startDate}
                    onChange={handleChange}
                    disabled={isSaving}
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="endDate" className="text-sm font-medium">
                    End Date *
                  </label>
                  <Input
                    id="endDate"
                    name="endDate"
                    type="date"
                    value={formData.endDate}
                    onChange={handleChange}
                    disabled={isSaving}
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="budget" className="text-sm font-medium">
                    Budget (Optional)
                  </label>
                  <Input
                    id="budget"
                    name="budget"
                    type="number"
                    placeholder="e.g., 5000"
                    value={formData.budget}
                    onChange={handleChange}
                    disabled={isSaving}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="description" className="text-sm font-medium">
                  Description (Optional)
                </label>
                <textarea
                  id="description"
                  name="description"
                  placeholder="Tell us about your trip..."
                  value={formData.description}
                  onChange={handleChange}
                  disabled={isSaving}
                  rows={4}
                  className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm"
                />
              </div>

              <div className="flex gap-4">
                <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                  disabled={isSaving}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
