'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'

const rings = [
  { label: 'Budget Health', value: 64, color: '#C4751A', scoreColor: '#C4751A' },
  { label: 'Eco Score', value: 82, color: '#5C7A5A', scoreColor: '#7AB87A' },
  { label: 'Safety Score', value: 91, color: '#2D8A6E', scoreColor: '#2D8A6E' },
  { label: 'Crowd Score', value: 70, color: '#8B6B3D', scoreColor: '#8B6B3D' },
]

export default function TripHealthPage() {
  const params = useParams<{ tripId: string }>()
  const [estimated] = useState(1000)
  const [actual, setActual] = useState(760)
  const [expenseInput, setExpenseInput] = useState('40')

  const budgetPct = Math.min(100, Math.round((actual / estimated) * 100))
  const showReplan = budgetPct >= 80

  const logExpense = () => {
    const delta = Number(expenseInput)
    if (!Number.isFinite(delta) || delta <= 0) return
    setActual((prev) => prev + delta)
    setExpenseInput('')
  }

  return (
    <div className="p-6 md:p-8 space-y-6">
      <h1 className="text-3xl font-bold editorial-heading">Trip Health • {params.tripId}</h1>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Nomad Score</CardTitle></CardHeader>
        <CardContent className="flex items-baseline gap-3">
          <p className="text-4xl font-bold" style={{ color: '#D4A843' }}>1,840</p>
          <p className="text-sm text-slate-600">Reward momentum this week</p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rings.map((ring) => (
          <Card key={ring.label}>
            <CardHeader className="pb-2"><CardTitle className="text-base">{ring.label}</CardTitle></CardHeader>
            <CardContent className="flex items-center gap-4">
              <svg width="66" height="66" viewBox="0 0 66 66" aria-hidden="true">
                <circle cx="33" cy="33" r="28" stroke="rgba(120,95,72,0.24)" strokeWidth="8" fill="none" />
                <circle
                  cx="33"
                  cy="33"
                  r="28"
                  stroke={ring.color}
                  strokeWidth="8"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={176}
                  strokeDashoffset={176 - (176 * ring.value) / 100}
                  transform="rotate(-90 33 33)"
                />
              </svg>
              <div>
                <p className="text-2xl font-semibold" style={{ color: ring.scoreColor }}>{ring.value}%</p>
                <Progress value={ring.value} className="mt-1" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Budget tension + expense log</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full"
              style={{
                width: `${budgetPct}%`,
                background: budgetPct >= 100 ? '#A85432' : budgetPct >= 80 ? '#C4751A' : '#4CAF82',
              }}
            />
          </div>
          <p className="text-sm text-slate-600">₹{actual} / ₹{estimated} ({budgetPct}%)</p>
          <div className="flex gap-2">
            <Input type="number" value={expenseInput} onChange={(e) => setExpenseInput(e.target.value)} placeholder="Expense amount" />
            <Button onClick={logExpense}>Log expense</Button>
          </div>
          {showReplan && (
            <Card className="border-amber-300 bg-amber-50">
              <CardContent className="pt-4 flex items-center justify-between gap-3">
                <p className="text-sm">Your budget is at {budgetPct}%. Replan the next days with cheaper alternatives?</p>
                <Button variant="outline">Smart replan</Button>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Black Mirror visualization</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="rounded-lg border p-3">
            <p className="font-medium">Current plan</p>
            <p>Rooftop dinner • Taxi transfers • Premium lounge</p>
          </div>
          <div className="rounded-lg border p-3" style={{ background: '#1E1810', borderColor: '#4A3A2A' }}>
            <p className="font-medium">At this pace</p>
            <p style={{ color: '#6B5A48' }}>Street food • Transit pass • Standard seating</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
