'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'
import { AlertCircle } from 'lucide-react'

const THEMES = ['Adventure', 'Beach', 'Cultural', 'Food', 'Hiking', 'Luxury', 'Budget', 'Family', 'Solo', 'Romantic']

export default function NewTripPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    destination: '',
    startDate: '',
    endDate: '',
    theme: '',
    budget: '',
    description: '',
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

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

    setIsLoading(true)

    try {
      const trip = await apiClient.trips.create({
        destination: formData.destination,
        start_date: formData.startDate,
        end_date: formData.endDate,
        theme: formData.theme,
        budget: formData.budget ? parseInt(formData.budget) : null,
        description: formData.description || null,
      })

      router.push(`/dashboard/trips/${trip.trip_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create trip')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Create New Trip</h1>
        <p className="text-slate-600 mb-8">Plan your next adventure with Nomadiq</p>

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
                    placeholder="e.g., Delhi, India"
                    value={formData.destination}
                    onChange={handleChange}
                    disabled={isLoading}
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
                    disabled={isLoading}
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
                    disabled={isLoading}
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
                    disabled={isLoading}
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
                    disabled={isLoading}
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
                  disabled={isLoading}
                  rows={4}
                  className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm"
                />
              </div>

              <div className="flex gap-4">
                <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      Creating...
                    </>
                  ) : (
                    'Create Trip'
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                  disabled={isLoading}
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
