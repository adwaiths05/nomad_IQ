'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { CloudSun, ArrowRight, Coins, BellRing, Sparkles } from 'lucide-react'
import { apiClient } from '../../../lib/api/client'
import type { Trip, ItineraryItem } from '../../../lib/api/types'

const now = new Date()

export default function DashboardPage() {
  const [showBriefing, setShowBriefing] = useState(true)
  const [trips, setTrips] = useState<Trip[]>([])
  const [activeTrip, setActiveTrip] = useState<Trip | null>(null)
  const [activeItinerary, setActiveItinerary] = useState<ItineraryItem[]>([])
  const [budgetPct, setBudgetPct] = useState(84)
  const [weatherLine, setWeatherLine] = useState('24°C • Clear')
  const [budgetLine, setBudgetLine] = useState('₹84,000 / ₹1,00,000')

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const tripData = await apiClient.trips.getAll()
        setTrips(tripData)
        const nowDate = new Date()
        const current =
          tripData.find((trip) => {
            const start = new Date(trip.start_date)
            const end = new Date(trip.end_date)
            return start <= nowDate && end >= nowDate
          }) || tripData[0] || null

        setActiveTrip(current)

        if (current) {
          const itinerary = await apiClient.itinerary.getByTrip(current.trip_id || current.id)
          setActiveItinerary(itinerary)

          try {
            const budget = await apiClient.budget.getByTrip(current.id)
            const estimated = Number(budget.estimated_total || 1000)
            const actual = Number(budget.actual_spent || 0)
            const pct = estimated > 0 ? Math.min(100, Math.round((actual / estimated) * 100)) : 84
            setBudgetPct(pct)
            setBudgetLine(`₹${actual.toLocaleString()} / ₹${estimated.toLocaleString()}`)
          } catch {
            const baseBudget = current.budget || 1000
            const utilization = Math.min(100, Math.max(35, Math.round((itinerary.length * 9.5) % 101)))
            setBudgetPct(Math.min(utilization, baseBudget > 0 ? utilization : 84))
          }

          try {
            const weather = await apiClient.weather.check(current.city, now.toISOString().slice(0, 10))
            const temp = weather.temperature_c != null ? `${weather.temperature_c}°C` : ''
            const condition = weather.weather || 'Clear'
            setWeatherLine([temp, condition].filter(Boolean).join(' • '))
          } catch {
            // Keep default weather text.
          }
        }
      } catch {
        // Keep graceful defaults when APIs are unavailable.
      }
    }

    loadDashboard()
  }, [])

  useEffect(() => {
    const dismissed = localStorage.getItem('nomad_briefing_seen') === 'true'
    const hour = new Date().getHours()
    if (dismissed || hour >= 20) {
      setShowBriefing(false)
    }
  }, [])

  const tensionColor = useMemo(() => {
    if (budgetPct >= 100) return 'bg-red-500'
    if (budgetPct >= 80) return 'bg-amber-500'
    if (budgetPct >= 60) return 'bg-emerald-500'
    return 'bg-teal-500'
  }, [budgetPct])

  const dismissBriefing = () => {
    localStorage.setItem('nomad_briefing_seen', 'true')
    setShowBriefing(false)
  }

  const openAmbientAi = (prompt: string) => {
    window.dispatchEvent(new CustomEvent('nomad-ai-open', { detail: { prompt } }))
  }

  return (
    <div className="p-6 md:p-8 space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600">Active intelligence for today&apos;s trip decisions</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() =>
              openAmbientAi(
                `What should I do next for ${activeTrip?.destination || activeTrip?.city || 'my trip'} with current budget and transit context?`
              )
            }
          >
            Ask AI in context
          </Button>
          <Link href="/plan">
            <Button className="bg-teal-600 hover:bg-teal-700">Open Trip Planner</Button>
          </Link>
        </div>
      </div>

      {showBriefing && (
        <Card className="border-l-4 border-l-teal-500">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between text-lg">
              <span className="flex items-center gap-2"><CloudSun className="h-5 w-5 text-teal-600" /> Good morning, Nomad Briefing</span>
              <Button variant="ghost" size="sm" onClick={dismissBriefing}>Dismiss</Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-slate-500">Today</p>
              <p className="font-semibold">{now.toLocaleDateString()}</p>
            </div>
            <div>
              <p className="text-slate-500">Weather</p>
              <p className="font-semibold">{weatherLine}</p>
            </div>
            <div>
              <p className="text-slate-500">Crowd warning</p>
              <p className="font-semibold">Mumbai local 11:30 spike</p>
            </div>
            <div>
              <p className="text-slate-500">Highlight</p>
              <p className="font-semibold">{activeItinerary[0]?.activity || 'Nezu Garden Walk'}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center justify-between">
            <span className="flex items-center gap-2"><Coins className="h-4 w-4" /> Budget Tension</span>
            <span className="text-sm">{budgetLine}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
            <div className={`h-full ${tensionColor} ${budgetPct >= 80 ? 'animate-pulse' : ''}`} style={{ width: `${budgetPct}%` }} />
          </div>
          <div className="flex items-center justify-between text-xs text-slate-600">
            <span>{budgetPct}% used</span>
            {budgetPct >= 80 && (
              <Link href="/trips/demo-trip/health">
                <Button size="sm" variant="outline">Replan cheaper alternatives</Button>
              </Link>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Active Trip Quick Card</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-slate-500">Destination</p>
              <p className="font-semibold">{activeTrip?.destination || 'Delhi'}</p>
            </div>
            <div>
              <p className="text-slate-500">Dates</p>
              <p className="font-semibold">
                {activeTrip
                  ? `${new Date(activeTrip.start_date).toLocaleDateString()} - ${new Date(activeTrip.end_date).toLocaleDateString()}`
                  : 'Mar 24 - Mar 29'}
              </p>
            </div>
            <div>
              <p className="text-slate-500">Next item</p>
              <p className="font-semibold">{activeItinerary[0]?.activity || 'India Gate at 09:30'}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Nomad Score</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{1600 + trips.length * 40}</p>
            <p className="text-xs text-slate-500 mt-1">Eco +420 • Budget +300 • Explorer +1120</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2"><BellRing className="h-4 w-4" /> Tripcast 48h Preview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Weather confidence is stable with one rain pocket on Day 2.</p>
            <p>Safety score remains high in all planned zones.</p>
            <Link href="/trips/demo-trip/tripcast" className="inline-flex items-center text-teal-700 font-medium">Open Tripcast <ArrowRight className="h-4 w-4 ml-1" /></Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2"><Sparkles className="h-4 w-4" /> Cross-trip Insight Teaser</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>&quot;You usually overspend on Day 2 after evening transit.&quot;</p>
            <Progress value={72} />
            <Badge variant="secondary">Pattern confidence 72%</Badge>
            <Link href="/profile" className="block text-teal-700 font-medium">See full insights</Link>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
