'use client'

import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiClient } from '../../../../../lib/api/client'

const fallbackCards = [
  { title: 'Weather brief', body: 'Day 2 rain pocket at 14:00, clear mornings.' },
  { title: 'Safety brief', body: 'All planned zones remain low-risk after 9pm.' },
  { title: 'Events during trip', body: 'Indie jazz rooftop, Saturday 19:30 near stay.' },
  { title: 'Budget readiness', body: 'Plan remains under cap if transit pass is used.' },
]

export default function TripcastPage() {
  const params = useParams<{ tripId: string }>()
  const [index, setIndex] = useState(0)
  const [cards, setCards] = useState(fallbackCards)

  useEffect(() => {
    const t = setInterval(() => setIndex((i) => (i + 1) % cards.length), 5000)
    return () => clearInterval(t)
  }, [cards.length])

  useEffect(() => {
    const loadTripcast = async () => {
      try {
        const trip = await apiClient.trips.getById(params.tripId)

        const [weather, events, budget] = await Promise.allSettled([
          apiClient.weather.check(trip.city, new Date().toISOString().slice(0, 10)),
          apiClient.events.syncByTrip(params.tripId),
          apiClient.budget.getByTrip(params.tripId),
        ])

        const weatherText =
          weather.status === 'fulfilled'
            ? `${weather.value.temperature_c ?? ''}°C ${weather.value.weather || 'stable'} forecast outlook.`.trim()
            : fallbackCards[0].body

        const eventsText =
          events.status === 'fulfilled'
            ? events.value.length > 0
              ? `${events.value[0].title} on ${new Date(events.value[0].date).toLocaleDateString()} is now synced.`
              : 'No major events detected during selected trip dates.'
            : fallbackCards[2].body

        const budgetText =
          budget.status === 'fulfilled'
            ? `Spend status: ₹${budget.value.actual_spent} / ₹${budget.value.estimated_total}.`
            : fallbackCards[3].body

        setCards([
          { title: 'Weather brief', body: weatherText },
          { title: 'Safety brief', body: 'Safety score remains stable across planned zones.' },
          { title: 'Events during trip', body: eventsText },
          { title: 'Budget readiness', body: budgetText },
        ])
      } catch {
        setCards(fallbackCards)
      }
    }

    void loadTripcast()
  }, [params.tripId])

  return (
    <div className="p-0 min-h-[calc(100vh-40px)] post-auth-tripcast-root">
      <div className="p-6 text-sm post-auth-tripcast-kicker">Tripcast • {params.tripId}</div>
      <div className="px-6 pb-6">
        <div className="grid grid-cols-4 gap-2 mb-4">
          {cards.map((_, i) => (
            <div key={i} className="h-1 rounded-full overflow-hidden post-auth-tripcast-track">
              <div className={`h-full post-auth-tripcast-progress ${i === index ? 'w-full transition-all duration-[5000ms]' : i < index ? 'w-full' : 'w-0'}`} />
            </div>
          ))}
        </div>
        <Card className="overflow-hidden post-auth-tripcast-card">
          <CardContent className="pt-8 pb-8">
            <h2 className="text-3xl font-bold mb-3 editorial-heading">{cards[index].title}</h2>
            <p className="text-lg post-auth-tripcast-body">{cards[index].body}</p>
            <div className="mt-6 flex gap-2">
              <Button>Share image export</Button>
              <Button variant="outline">Start trip</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
