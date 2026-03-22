'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'

export default function PlanPage() {
  const [prompt, setPrompt] = useState('')
  const [pace, setPace] = useState('moderate')
  const [eventFirst, setEventFirst] = useState(false)
  const [antiTourist, setAntiTourist] = useState(false)
  const [pressureOpen, setPressureOpen] = useState(false)
  const [anchor, setAnchor] = useState('')
  const [budget] = useState([1400])

  return (
    <div className="p-6 md:p-8 space-y-6">
      <h1 className="text-3xl font-bold text-slate-900">Trip Planner</h1>

      <Card>
        <CardHeader>
          <CardTitle>Autopilot NL input (#13)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Plan around rainy Tokyo + art museums + 5 days" />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {['strict', 'moderate', 'light'].map((mode) => (
              <Button key={mode} variant={pace === mode ? 'default' : 'outline'} onClick={() => setPace(mode)}>
                Pace: {mode}
              </Button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-lg border p-3">
              <p className="text-sm font-medium mb-2">Reverse anchor planning (#15)</p>
              <Input value={anchor} onChange={(e) => setAnchor(e.target.value)} placeholder="Pin unmissable place/event" />
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-sm font-medium mb-2">Event-first flow (#17)</p>
              <div className="flex items-center justify-between"><span className="text-sm text-slate-600">Plan around event cards</span><Switch checked={eventFirst} onCheckedChange={setEventFirst} /></div>
            </div>
          </div>

          <div className="rounded-lg border p-3 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Anti-tourist mode (#19)</p>
              <p className="text-xs text-slate-500">Avoid high crowd-score venues</p>
            </div>
            <Switch checked={antiTourist} onCheckedChange={setAntiTourist} />
          </div>

          <div className="rounded-lg border p-3">
            <p className="text-sm font-medium">Nomad Autopilot budget</p>
            <p className="text-xs text-slate-500 mb-2">€{budget[0]} target · date range and destination auto-selected</p>
            <Slider value={budget} min={400} max={4000} step={50} disabled />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button>Generate plan</Button>
            <Button variant="outline" onClick={() => setPressureOpen((v) => !v)}>Stress test this plan (#21)</Button>
          </div>

          {pressureOpen && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
              <Card><CardContent className="pt-4"><Badge>Rain scenario</Badge><p className="text-sm mt-2">Day 2 moved to indoor galleries.</p></CardContent></Card>
              <Card><CardContent className="pt-4"><Badge variant="secondary">Overspend +30%</Badge><p className="text-sm mt-2">2 luxury meals replaced.</p></CardContent></Card>
              <Card><CardContent className="pt-4"><Badge variant="outline">Event cancelled</Badge><p className="text-sm mt-2">Anchor swapped to nearby festival.</p></CardContent></Card>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
