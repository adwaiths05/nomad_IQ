'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader, BookOpen, MapPin, Users } from 'lucide-react'
import type { TravelGuide } from '@/lib/api/types'

export default function GuidesPage() {
  const [guides, setGuides] = useState<TravelGuide[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchGuides()
  }, [])

  const fetchGuides = async () => {
    try {
      setLoading(true)
      const data = await apiClient.guides.getAll()
      setGuides(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch guides')
    } finally {
      setLoading(false)
    }
  }

  const filteredGuides = guides.filter(
    (guide) =>
      guide.destination.toLowerCase().includes(searchTerm.toLowerCase()) ||
      guide.title.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Travel Guides</h1>
        <p className="text-slate-600">Explore curated travel guides and insider tips</p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <Input
          placeholder="Search guides by destination or title..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-md"
        />
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      ) : error ? (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      ) : filteredGuides.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-600">
              {searchTerm ? 'No guides match your search.' : 'No guides available yet.'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredGuides.map((guide) => (
            <Card key={guide.guide_id} className="hover:shadow-lg transition-shadow flex flex-col">
              <CardHeader>
                <CardTitle className="line-clamp-2">{guide.title}</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 space-y-4">
                {/* Destination */}
                <div className="flex items-start gap-2">
                  <MapPin className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-slate-600">Destination</p>
                    <p className="text-slate-900 font-semibold">{guide.destination}</p>
                  </div>
                </div>

                {/* Duration */}
                <div className="flex items-start gap-2">
                  <BookOpen className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-slate-600">Best Duration</p>
                    <p className="text-slate-900">{guide.duration_days} days</p>
                  </div>
                </div>

                {/* Best Time */}
                <div>
                  <p className="text-sm text-slate-600 mb-1">Best Time to Visit</p>
                  <p className="text-slate-900">{guide.best_time}</p>
                </div>

                {/* Description */}
                <div>
                  <p className="text-sm text-slate-600 line-clamp-3">{guide.description}</p>
                </div>

                {/* Highlights */}
                {guide.highlights && (
                  <div>
                    <p className="text-sm text-slate-600 mb-2">Highlights</p>
                    <div className="space-y-1">
                      {guide.highlights.split(',').slice(0, 3).map((highlight, idx) => (
                        <p key={idx} className="text-sm text-slate-700">
                          • {highlight.trim()}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tips */}
                {guide.local_tips && (
                  <div className="bg-blue-50 rounded-lg p-3">
                    <p className="text-sm font-semibold text-blue-900 mb-1">Local Tip</p>
                    <p className="text-sm text-blue-800 line-clamp-2">{guide.local_tips}</p>
                  </div>
                )}

                {/* Read More Button */}
                <Button variant="outline" className="w-full mt-4">
                  Read Full Guide
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
