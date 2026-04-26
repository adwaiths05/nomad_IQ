'use client'

import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { apiClient } from '../../../../../lib/api/client'
import type { ItineraryItem } from '../../../../../lib/api/types'

function ConfidenceRing({ value }: { value: number }) {
  const radius = 12
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value / 100) * circumference
  const tone = value < 50 ? '#ef4444' : value < 75 ? '#f59e0b' : '#14b8a6'

  return (
    <svg width="28" height="28" viewBox="0 0 28 28" aria-label={`${value}% confidence`}>
      <circle cx="14" cy="14" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="2" />
      <circle
        cx="14"
        cy="14"
        r={radius}
        fill="none"
        stroke={tone}
        strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform="rotate(-90 14 14)"
      />
    </svg>
  )
}

type EnrichedItineraryItem = ItineraryItem & {
  confidence: number
  why: string
  score: string
}

export default function ItineraryDetailPage() {
  const params = useParams<{ tripId: string }>()
  const [items, setItems] = useState<ItineraryItem[]>([])
  const [openWhy, setOpenWhy] = useState<string | null>(null)
  const [showEcoDrawer, setShowEcoDrawer] = useState(false)
  const [remoteMode, setRemoteMode] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiClient.itinerary.getByTrip(params.tripId)
        setItems(data)
      } catch {
        setItems([])
      }
    }

    if (params.tripId) {
      load()
    }
  }, [params.tripId])

  const enriched = useMemo<EnrichedItineraryItem[]>(
    () =>
      items.map((item, idx) => ({
        ...item,
        confidence: Math.min(96, 58 + ((idx + 2) * 11) % 40),
        why: 'Chosen by score blend: crowd, proximity, timing, and preference match.',
        score: `crowd ${(2 + (idx % 4) * 0.7).toFixed(1)} • visual ${(7.8 + (idx % 3) * 0.5).toFixed(1)} • distance ${300 + idx * 120}m`,
      })),
    [items]
  )

  const grouped = useMemo<Record<number, EnrichedItineraryItem[]>>(
    () =>
      enriched.reduce<Record<number, EnrichedItineraryItem[]>>((acc, item) => {
        const dayNumber = item.day ?? 1
        if (!acc[dayNumber]) {
          acc[dayNumber] = []
        }
        acc[dayNumber].push(item)
        return acc
      }, {}),
    [enriched]
  )

  const timeline = useMemo(
    () =>
      enriched
        .slice()
        .sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''))
        .slice(0, 10),
    [enriched]
  )

  const openAmbientAi = (prompt: string) => {
    window.dispatchEvent(new CustomEvent('nomad-ai-open', { detail: { prompt } }))
  }

  return (
    <div className="p-6 md:p-8 space-y-4">
      <h1 className="text-3xl font-bold">Itinerary • {params.tripId}</h1>

      <Card>
        <CardContent className="pt-4 flex items-center justify-between gap-4">
          <div className="w-full">
            <p className="text-xs text-slate-500">Budget tension</p>
            <div className="h-1.5 rounded-full bg-slate-100 mt-1 overflow-hidden">
              <div className="h-full w-[84%] bg-amber-500" />
            </div>
          </div>
          <Button size="sm" variant="outline">Cheaper alternatives</Button>
          <div className="flex items-center gap-2 text-sm"><span>Remote mode</span><Switch checked={remoteMode} onCheckedChange={setRemoteMode} /></div>
        </CardContent>
      </Card>

      <div className="sticky top-0 z-10 rounded-lg border bg-white p-3">
        <p className="text-sm font-medium">Timeline scrubber</p>
        <div className="mt-2 flex items-center gap-3">
          {timeline.map((item) => (
            <button key={item.item_id} className="h-8 w-8 rounded-full bg-teal-100 text-xs">
              {(item.start_time || '09:00').slice(0, 2)}
            </button>
          ))}
        </div>
      </div>

      {Object.keys(grouped).length === 0 && (
        <Card>
          <CardContent className="pt-6 text-sm text-slate-600">No itinerary items yet for this trip.</CardContent>
        </Card>
      )}

      {Object.entries(grouped)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([day, dayItems]) => (
          <div key={day} className="space-y-3">
            <h2 className="text-lg font-semibold">Day {day}</h2>
            {dayItems.map((item) => (
              <Card key={item.item_id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>
                      {(item.start_time || '09:00').slice(0, 5)} • {item.activity}
                    </span>
                    <div className="flex items-center gap-2">
                      <ConfidenceRing value={item.confidence} />
                      <Badge>{item.confidence}% confidence</Badge>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      size="sm"
                      onClick={() =>
                        openAmbientAi(
                          `I am on itinerary day ${day}, item ${item.activity}. Suggest the best next move with live transit and budget awareness.`
                        )
                      }
                    >
                      Ask AI here
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setOpenWhy(openWhy === (item.item_id || item.id) ? null : (item.item_id || item.id))}
                    >
                      Why this?
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setShowEcoDrawer((v) => !v)}>
                      Eco route drawer
                    </Button>
                    <Badge variant="outline">Micro feedback marks</Badge>
                    <Badge variant="outline">Living map toggle</Badge>
                  </div>
                  {openWhy === (item.item_id || item.id) && (
                    <div className="rounded-lg border bg-slate-50 p-3 text-sm">
                      <p>{item.why}</p>
                      <p className="text-slate-500 mt-1">{item.score}</p>
                    </div>
                  )}
                  {showEcoDrawer && (
                    <div className="rounded-lg border p-3 text-sm grid grid-cols-1 md:grid-cols-3 gap-2">
                      <div className="rounded border p-2">Fastest: 22m • 5.6kg CO2</div>
                      <div className="rounded border p-2">Cheapest: ₹2.8 • 7.1kg CO2</div>
                      <div className="rounded border border-teal-400 p-2">Eco: 8.1kg CO2 = 0.3 trees saved</div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ))}
    </div>
  )
}
