'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { apiClient } from '../../../lib/api/client'
import type { MemoryRead } from '../../../lib/api/types'

type ProfileDetails = {
  homeCity: string
  nationality: string
  languages: string
  travelStyle: string
  dietaryNeeds: string
  accessibilityNeeds: string
  emergencyContact: string
  preferredAirline: string
  seatPreference: string
  accommodationType: string
  budgetComfortRange: string
  bio: string
}

const defaultDetails: ProfileDetails = {
  homeCity: '',
  nationality: '',
  languages: 'English',
  travelStyle: 'Balanced explorer',
  dietaryNeeds: '',
  accessibilityNeeds: '',
  emergencyContact: '',
  preferredAirline: '',
  seatPreference: 'Window',
  accommodationType: 'Boutique hotel',
  budgetComfortRange: '1200-2000 INR / week',
  bio: '',
}

export default function ProfilePage() {
  const [pace, setPace] = useState('Moderate')
  const [eco, setEco] = useState(true)
  const [remote, setRemote] = useState(false)
  const [insights, setInsights] = useState<MemoryRead[]>([])
  const [details, setDetails] = useState<ProfileDetails>(defaultDetails)
  const [savedAt, setSavedAt] = useState<string | null>(null)

  useEffect(() => {
    const profile = localStorage.getItem('onboarding_profile')
    if (!profile) return
    try {
      const parsed = JSON.parse(profile) as { pace?: string; ecoMode?: boolean; remoteHours?: string }
      if (parsed.pace) {
        setPace(parsed.pace.charAt(0).toUpperCase() + parsed.pace.slice(1))
      }
      if (typeof parsed.ecoMode === 'boolean') {
        setEco(parsed.ecoMode)
      }
      if (parsed.remoteHours) {
        setRemote(true)
      }
    } catch {
      // Ignore malformed local onboarding state.
    }
  }, [])

  useEffect(() => {
    const existing = localStorage.getItem('profile_details')
    if (!existing) return
    try {
      const parsed = JSON.parse(existing) as Partial<ProfileDetails>
      setDetails((prev) => ({ ...prev, ...parsed }))
    } catch {
      // Ignore malformed stored profile details.
    }
  }, [])

  useEffect(() => {
    const profile = localStorage.getItem('onboarding_profile')
    if (!profile) return
    try {
      const parsed = JSON.parse(profile) as Record<string, unknown>
      localStorage.setItem('onboarding_profile', JSON.stringify({ ...parsed, ecoMode: eco, remoteMode: remote }))
    } catch {
      // Ignore malformed local onboarding state.
    }
  }, [eco, remote])

  const updateDetail = <K extends keyof ProfileDetails>(key: K, value: ProfileDetails[K]) => {
    setDetails((prev) => ({ ...prev, [key]: value }))
  }

  const saveDetails = () => {
    localStorage.setItem('profile_details', JSON.stringify(details))
    setSavedAt(new Date().toLocaleTimeString())
  }

  useEffect(() => {
    const loadInsights = async () => {
      const userId = localStorage.getItem('current_user_id') || undefined
      try {
        const data = await apiClient.memory.search({
          query: 'overspend pattern skipped activities crowd preference',
          user_id: userId,
          limit: 3,
        })
        setInsights(data)
      } catch {
        setInsights([])
      }
    }

    void loadInsights()
  }, [])

  return (
    <div className="p-6 md:p-8 space-y-6">
      <h1 className="text-3xl font-bold">Profile + Insights</h1>

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="insights">Cross-trip insights</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Traveler preferences</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between"><span>Pace preference</span><span className="font-medium">{pace}</span></div>
              <div className="flex items-center justify-between"><span>Eco mode</span><Switch checked={eco} onCheckedChange={setEco} /></div>
              <div className="flex items-center justify-between"><span>Remote-work mode</span><Switch checked={remote} onCheckedChange={setRemote} /></div>
              <div className="rounded-lg border p-3">
                <p className="font-semibold text-2xl">Nomad Score 1840</p>
                <p className="text-xs text-slate-500">History: +60 last trip, +110 this month</p>
                <div className="mt-3 h-8 flex items-end gap-1">
                  {[40, 45, 52, 58, 61, 67, 72].map((h, i) => (
                    <span key={i} className="w-3 rounded-sm bg-teal-400/70" style={{ height: `${h}%` }} />
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="details" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Extended traveler profile</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium">Home city</label>
                  <Input value={details.homeCity} onChange={(e) => updateDetail('homeCity', e.target.value)} placeholder="Bengaluru" />
                </div>
                <div>
                  <label className="text-sm font-medium">Nationality</label>
                  <Input value={details.nationality} onChange={(e) => updateDetail('nationality', e.target.value)} placeholder="Indian" />
                </div>
                <div>
                  <label className="text-sm font-medium">Languages</label>
                  <Input value={details.languages} onChange={(e) => updateDetail('languages', e.target.value)} placeholder="English, Hindi" />
                </div>
                <div>
                  <label className="text-sm font-medium">Travel style</label>
                  <Input value={details.travelStyle} onChange={(e) => updateDetail('travelStyle', e.target.value)} placeholder="Culture-first slow travel" />
                </div>
                <div>
                  <label className="text-sm font-medium">Preferred airline</label>
                  <Input value={details.preferredAirline} onChange={(e) => updateDetail('preferredAirline', e.target.value)} placeholder="Any Star Alliance" />
                </div>
                <div>
                  <label className="text-sm font-medium">Seat preference</label>
                  <Input value={details.seatPreference} onChange={(e) => updateDetail('seatPreference', e.target.value)} placeholder="Window" />
                </div>
                <div>
                  <label className="text-sm font-medium">Accommodation type</label>
                  <Input value={details.accommodationType} onChange={(e) => updateDetail('accommodationType', e.target.value)} placeholder="Boutique hotel" />
                </div>
                <div>
                  <label className="text-sm font-medium">Comfort budget range</label>
                  <Input value={details.budgetComfortRange} onChange={(e) => updateDetail('budgetComfortRange', e.target.value)} placeholder="1200-2000 INR / week" />
                </div>
                <div>
                  <label className="text-sm font-medium">Dietary needs</label>
                  <Input value={details.dietaryNeeds} onChange={(e) => updateDetail('dietaryNeeds', e.target.value)} placeholder="Vegetarian" />
                </div>
                <div>
                  <label className="text-sm font-medium">Accessibility needs</label>
                  <Input value={details.accessibilityNeeds} onChange={(e) => updateDetail('accessibilityNeeds', e.target.value)} placeholder="Step-free paths" />
                </div>
                <div className="md:col-span-2">
                  <label className="text-sm font-medium">Emergency contact</label>
                  <Input value={details.emergencyContact} onChange={(e) => updateDetail('emergencyContact', e.target.value)} placeholder="Name, phone, relation" />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium">Traveler bio</label>
                <Textarea
                  value={details.bio}
                  onChange={(e) => updateDetail('bio', e.target.value)}
                  placeholder="I prefer local neighborhoods, walkable itineraries, and food-first planning."
                />
              </div>

              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-500">{savedAt ? `Saved at ${savedAt}` : 'Changes are saved locally for now.'}</p>
                <Button type="button" onClick={saveDetails}>Save details</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="insights" className="space-y-3">
          {insights.length === 0 && (
            <Card>
              <CardContent className="pt-6">
                <p className="font-medium">You always overspend Day 2</p>
                <p className="text-sm text-slate-500 mt-1">3 of 4 trips crossed 80% budget after evening transit.</p>
              </CardContent>
            </Card>
          )}
          {insights.map((insight) => (
            <Card key={insight.id}>
              <CardContent className="pt-6">
                <p className="font-medium">Cross-trip pattern</p>
                <p className="text-sm text-slate-500 mt-1">{insight.text}</p>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
