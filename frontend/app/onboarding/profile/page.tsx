'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'

export default function OnboardingProfilePage() {
  const router = useRouter()
  const [pace, setPace] = useState('moderate')
  const [budgetSensitivity, setBudgetSensitivity] = useState([60])
  const [ecoMode, setEcoMode] = useState(true)
  const [remoteHours, setRemoteHours] = useState('09:00-13:00')
  const [cultureInterest, setCultureInterest] = useState([70])
  const [foodInterest, setFoodInterest] = useState([80])

  const handleContinue = () => {
    localStorage.setItem(
      'onboarding_profile',
      JSON.stringify({ pace, budgetSensitivity: budgetSensitivity[0], ecoMode, remoteHours, cultureInterest: cultureInterest[0], foodInterest: foodInterest[0] })
    )
    router.push('/onboarding/identity')
  }

  return (
    <div className="max-w-3xl mx-auto p-6 md:p-10">
      <p className="text-sm text-slate-500 mb-3">Step 1 of 2</p>
      <h1 className="text-3xl font-bold text-slate-900 mb-6">Profile setup</h1>
      <Card>
        <CardHeader>
          <CardTitle>Shape how Nomadiq plans your trip</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <p className="text-sm font-medium mb-2">Pace selector</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { key: 'slow', label: 'Tortoise' },
                { key: 'moderate', label: 'Balanced' },
                { key: 'fast', label: 'Rocket' },
              ].map((option) => (
                <Button key={option.key} variant={pace === option.key ? 'default' : 'outline'} onClick={() => setPace(option.key)}>
                  {option.label}
                </Button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-sm font-medium mb-2">Budget sensitivity: {budgetSensitivity[0]}%</p>
            <Slider value={budgetSensitivity} onValueChange={setBudgetSensitivity} min={0} max={100} step={1} />
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="font-medium">Eco preference</p>
              <p className="text-xs text-slate-500">Prefer lower-CO2 routes and stays</p>
            </div>
            <Switch checked={ecoMode} onCheckedChange={setEcoMode} />
          </div>

          <div>
            <p className="text-sm font-medium mb-2">Remote work hours</p>
            <Input value={remoteHours} onChange={(e) => setRemoteHours(e.target.value)} />
          </div>

          <div>
            <p className="text-sm font-medium mb-2">Culture interest: {cultureInterest[0]}%</p>
            <Slider value={cultureInterest} onValueChange={setCultureInterest} min={0} max={100} step={1} />
          </div>

          <div>
            <p className="text-sm font-medium mb-2">Food interest: {foodInterest[0]}%</p>
            <Slider value={foodInterest} onValueChange={setFoodInterest} min={0} max={100} step={1} />
          </div>

          <Button className="w-full" onClick={handleContinue}>Continue to identity</Button>
        </CardContent>
      </Card>
    </div>
  )
}
