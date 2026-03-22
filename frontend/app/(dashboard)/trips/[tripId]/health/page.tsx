'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'

const rings = [
  { label: 'Budget Health', value: 64 },
  { label: 'Eco Score', value: 82 },
  { label: 'Safety Score', value: 91 },
  { label: 'Crowd Score', value: 70 },
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
      <h1 className="text-3xl font-bold">Trip Health • {params.tripId}</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rings.map((ring) => (
          <Card key={ring.label}>
            <CardHeader className="pb-2"><CardTitle className="text-base">{ring.label} (#5)</CardTitle></CardHeader>
            <CardContent>
              <Progress value={ring.value} />
              <p className="text-sm mt-2">{ring.value}%</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Budget tension + expense log</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div className={`h-full ${budgetPct >= 100 ? 'bg-red-500' : budgetPct >= 80 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${budgetPct}%` }} />
          </div>
          <p className="text-sm text-slate-600">€{actual} / €{estimated} ({budgetPct}%)</p>
          <div className="flex gap-2">
            <Input type="number" value={expenseInput} onChange={(e) => setExpenseInput(e.target.value)} placeholder="Expense amount" />
            <Button onClick={logExpense}>Log expense</Button>
          </div>
          {showReplan && (
            <Card className="border-amber-300 bg-amber-50">
              <CardContent className="pt-4 flex items-center justify-between gap-3">
                <p className="text-sm">Your budget is at {budgetPct}%. Replan the next days with cheaper alternatives?</p>
                <Button variant="outline">Smart replan (#6)</Button>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Black Mirror visualization (#22)</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="rounded-lg border p-3">
            <p className="font-medium">Current plan</p>
            <p>Rooftop dinner • Taxi transfers • Premium lounge</p>
          </div>
          <div className="rounded-lg border border-amber-300 bg-amber-50 p-3">
            <p className="font-medium">At this pace</p>
            <p>Street food • Transit pass • Standard seating</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
