'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { apiClient } from '../../../lib/api/client'
import type { MemoryRead } from '../../../lib/api/types'

export default function ProfilePage() {
  const [pace, setPace] = useState('Moderate')
  const [eco, setEco] = useState(true)
  const [remote, setRemote] = useState(false)
  const [insights, setInsights] = useState<MemoryRead[]>([])

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
    const profile = localStorage.getItem('onboarding_profile')
    if (!profile) return
    try {
      const parsed = JSON.parse(profile) as Record<string, unknown>
      localStorage.setItem('onboarding_profile', JSON.stringify({ ...parsed, ecoMode: eco, remoteMode: remote }))
    } catch {
      // Ignore malformed local onboarding state.
    }
  }, [eco, remote])

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
          <TabsTrigger value="insights">Cross-trip insights (#24)</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Traveler preferences</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between"><span>Pace preference</span><span className="font-medium">{pace}</span></div>
              <div className="flex items-center justify-between"><span>Eco mode</span><Switch checked={eco} onCheckedChange={setEco} /></div>
              <div className="flex items-center justify-between"><span>Remote-work mode</span><Switch checked={remote} onCheckedChange={setRemote} /></div>
              <div className="rounded-lg border p-3">
                <p className="font-semibold text-2xl">Nomad Score 1840 (#23)</p>
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
