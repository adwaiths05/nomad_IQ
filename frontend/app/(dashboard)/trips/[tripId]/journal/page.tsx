'use client'

import { useParams } from 'next/navigation'
import { Card, CardContent } from '@/components/ui/card'

const chapters = [
  {
    day: 'Day 1',
    date: 'Mar 24',
    city: 'Tokyo',
    text: 'You began slowly, drifting from temple silence to narrow alleys where lunch came as a surprise. By dusk, your pace quickened but your choices stayed light, and that kept both budget and energy in balance.',
  },
  {
    day: 'Day 2',
    date: 'Mar 25',
    city: 'Tokyo',
    text: 'A rain pocket moved you indoors, but the plan adapted cleanly. The afternoon became galleries and coffee, and your evening route reduced transit friction without removing the highlights.',
  },
]

export default function JournalPage() {
  const params = useParams<{ tripId: string }>()

  return (
    <div className="p-6 md:p-8 space-y-6">
      <h1 className="text-3xl font-bold">AI Journal • {params.tripId} (#14)</h1>
      <p className="text-slate-600">Auto-generated end-of-day narrative with chapter layout.</p>
      {chapters.map((chapter) => (
        <Card key={chapter.day}>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{chapter.day} • {chapter.date} • {chapter.city}</p>
            <p className="mt-3 text-lg leading-8 text-slate-800" style={{ fontFamily: 'Georgia, Times New Roman, serif' }}>{chapter.text}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
