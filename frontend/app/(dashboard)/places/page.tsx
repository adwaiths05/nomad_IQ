'use client'

import { useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { apiClient } from '../../../lib/api/client'
import type { PlaceRead } from '../../../lib/api/types'

const INDIA_CITIES = [
  'Delhi',
  'Mumbai',
  'Bengaluru',
  'Chennai',
  'Kolkata',
  'Hyderabad',
  'Pune',
  'Ahmedabad',
  'Jaipur',
  'Kochi',
  'Goa',
  'Varanasi',
]

export default function PlacesPage() {
  const [city, setCity] = useState('Bengaluru')
  const [visual, setVisual] = useState([7])
  const [crowdMax, setCrowdMax] = useState([4])
  const [safety, setSafety] = useState([7])
  const [costMax, setCostMax] = useState([120])
  const [productive, setProductive] = useState(false)
  const [antiTourist, setAntiTourist] = useState(true)
  const [places, setPlaces] = useState<PlaceRead[]>([])

  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        const data = await apiClient.places.search({
          city,
          category: antiTourist ? 'hidden-gem' : undefined,
          productive_only: productive,
        })
        setPlaces(data)
      } catch {
        setPlaces([])
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [city, productive, antiTourist, visual, crowdMax, safety, costMax])

  const filteredPlaces = useMemo(
    () =>
      places.filter((place) => {
        const visualScore = place.productive_score ?? 7
        const crowdScore = place.crowd_score ?? 5
        const safetyScore = place.safety_score ?? 7
        const dailyCost = place.cost_per_day ?? 100
        return (
          visualScore >= visual[0] &&
          crowdScore <= crowdMax[0] &&
          safetyScore >= safety[0] &&
          dailyCost <= costMax[0]
        )
      }),
    [places, visual, crowdMax, safety, costMax]
  )

  return (
    <div className="p-6 md:p-8 space-y-6">
      <h1 className="text-3xl font-bold">Place Discovery</h1>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">India city picker</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <p>City</p>
              <select
                className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              >
                {INDIA_CITIES.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            <p className="text-xs text-slate-500">Showing India-only destinations and place suggestions.</p>
            <div className="pt-2 border-t border-slate-200">
              <p className="font-medium mb-3">Score filters</p>
            </div>
            <div><p>Visual score: {visual[0]}</p><Slider value={visual} onValueChange={setVisual} min={0} max={10} step={1} /></div>
            <div><p>Crowd score max: {crowdMax[0]}</p><Slider value={crowdMax} onValueChange={setCrowdMax} min={0} max={10} step={1} /></div>
            <div><p>Safety score: {safety[0]}</p><Slider value={safety} onValueChange={setSafety} min={0} max={10} step={1} /></div>
            <div><p>Cost/day max: ₹{costMax[0]}</p><Slider value={costMax} onValueChange={setCostMax} min={0} max={200} step={5} /></div>
            <div className="flex items-center justify-between"><span>Productive spots mode</span><Switch checked={productive} onCheckedChange={setProductive} /></div>
            <div className="flex items-center justify-between"><span>Anti-tourist filter</span><Switch checked={antiTourist} onCheckedChange={setAntiTourist} /></div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {filteredPlaces.length === 0 && (
            <Card>
              <CardContent className="pt-4 text-sm text-slate-600">No places matched these filters.</CardContent>
            </Card>
          )}
          {filteredPlaces.map((place) => (
            <Card key={place.id}>
              <CardContent className="pt-4">
                <p className="font-semibold">{place.name}</p>
                <p className="text-xs text-slate-500 mt-2">
                  Visual {place.productive_score ?? 7} • Crowd {place.crowd_score ?? 5} • Safety {place.safety_score ?? 7}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
