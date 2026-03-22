'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'

const personas = ['Urban Explorer', 'Slow Nomad', 'Culture Hunter', 'Outdoor Optimizer']

export default function OnboardingIdentityPage() {
  const router = useRouter()
  const [persona, setPersona] = useState(personas[0])
  const [riskTolerance, setRiskTolerance] = useState([45])
  const [antiTourist, setAntiTourist] = useState(false)

  const completeOnboarding = () => {
    localStorage.setItem(
      'onboarding_identity',
      JSON.stringify({ persona, riskTolerance: riskTolerance[0], antiTourist })
    )
    localStorage.setItem('onboarding_completed', 'true')
    router.push('/dashboard')
  }

  return (
    <div className="max-w-3xl mx-auto p-6 md:p-10">
      <p className="text-sm text-slate-500 mb-3">Step 2 of 2</p>
      <h1 className="text-3xl font-bold text-slate-900 mb-6">Traveler identity reveal</h1>
      <Card>
        <CardHeader>
          <CardTitle>Choose your travel persona</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {personas.map((p) => (
              <button
                key={p}
                className={`rounded-lg border p-4 text-left transition ${persona === p ? 'border-teal-600 bg-teal-50' : 'border-slate-200 bg-white'}`}
                onClick={() => setPersona(p)}
              >
                <p className="font-semibold">{p}</p>
                <p className="text-xs text-slate-500 mt-1">Persona type card reveal</p>
              </button>
            ))}
          </div>

          <div>
            <p className="text-sm font-medium mb-2">Risk tolerance: {riskTolerance[0]}%</p>
            <Slider value={riskTolerance} onValueChange={setRiskTolerance} min={0} max={100} step={1} />
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="font-medium">Anti-tourist mode</p>
              <p className="text-xs text-slate-500">De-prioritize crowded landmarks (#19)</p>
            </div>
            <Switch checked={antiTourist} onCheckedChange={setAntiTourist} />
          </div>

          <Button className="w-full" onClick={completeOnboarding}>Finish onboarding</Button>
        </CardContent>
      </Card>
    </div>
  )
}
