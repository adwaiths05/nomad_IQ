'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '../../../lib/api/client'
import type { Trip } from '../../../lib/api/types'

export default function TripsPage() {
  const [tab, setTab] = useState('active')
  const [trips, setTrips] = useState<Trip[]>([])

  useEffect(() => {
    const loadTrips = async () => {
      try {
        const data = await apiClient.trips.getAll()
        setTrips(data)
      } catch {
        setTrips([])
      }
    }

    loadTrips()
  }, [])

  const grouped = useMemo(() => {
    const now = new Date()
    return {
      active: trips.filter((trip) => new Date(trip.start_date) <= now && new Date(trip.end_date) >= now),
      upcoming: trips.filter((trip) => new Date(trip.start_date) > now),
      past: trips.filter((trip) => new Date(trip.end_date) < now),
    }
  }, [trips])

  const filtered = grouped[tab as keyof typeof grouped] || []

  return (
    <div className="p-6 md:p-8 space-y-6">
      <h1 className="text-3xl font-bold text-slate-900">Trips</h1>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="past">Past</TabsTrigger>
        </TabsList>

        <TabsContent value={tab} className="space-y-3">
          {filtered.length === 0 && (
            <Card>
              <CardContent className="pt-6 text-sm text-slate-600">
                No {tab} trips yet.
              </CardContent>
            </Card>
          )}

          {filtered.map((trip) => (
            <Card key={trip.trip_id}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{trip.destination}</span>
                  <Badge>Nomad Score {1600 + ((trip.destination || trip.city).length % 9) * 35}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                <Link href={`/trips/${trip.trip_id}/itinerary`} className="text-teal-700 text-sm font-medium">Open itinerary</Link>
                <Link href={`/trips/${trip.trip_id}/health`} className="text-teal-700 text-sm font-medium">Trip health</Link>
                <Link href={`/trips/${trip.trip_id}/tripcast`} className="text-teal-700 text-sm font-medium">Tripcast</Link>
                <Link href={`/trips/${trip.trip_id}/journal`} className="text-teal-700 text-sm font-medium">Journal</Link>
                {tab !== 'active' && <Badge variant="secondary">Time Capsule draft (#25)</Badge>}
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
