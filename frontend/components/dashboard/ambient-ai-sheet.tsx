'use client'

import { useEffect, useMemo, useState } from 'react'
import { usePathname, useSearchParams, useRouter } from 'next/navigation'
import { Loader2, MessageSquare, Sparkles, X } from 'lucide-react'

import { useAuth } from '@/lib/context/auth-context'
import { apiClient } from '@/lib/api/client'
import type { AmbientAssistResponse, Trip } from '@/lib/api/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'

function detectScreen(pathname: string): string {
  if (pathname.includes('/itinerary')) return 'itinerary'
  if (pathname.includes('/tripcast')) return 'tripcast'
  if (pathname.includes('/health')) return 'trip_health'
  if (pathname.includes('/places')) return 'place_discovery'
  if (pathname.includes('/plan')) return 'trip_planner'
  if (pathname.includes('/profile')) return 'profile'
  return 'dashboard'
}

function activeTripFromPath(pathname: string): string | null {
  const match = pathname.match(/\/trips\/([^/]+)/)
  return match?.[1] ?? null
}

export function AmbientAiSheet() {
  const { user } = useAuth()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()

  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('What should I do now?')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<AmbientAssistResponse | null>(null)
  const [trips, setTrips] = useState<Trip[]>([])
  const [activeTripId, setActiveTripId] = useState<string | null>(null)
  const [chips, setChips] = useState<string[]>([])
  const [expandedForQuery, setExpandedForQuery] = useState('')

  const screen = useMemo(() => detectScreen(pathname), [pathname])

  useEffect(() => {
    const fromUrl = searchParams.get('assistant') === 'open'
    if (fromUrl) {
      setOpen(true)
    }
  }, [searchParams])

  useEffect(() => {
    const loadTrips = async () => {
      try {
        const rows = await apiClient.trips.getAll()
        setTrips(rows)

        const fromPath = activeTripFromPath(pathname)
        if (fromPath) {
          setActiveTripId(fromPath)
          return
        }

        if (rows.length > 0) {
          setActiveTripId(rows[0].id || rows[0].trip_id || null)
        }
      } catch {
        setTrips([])
      }
    }

    loadTrips()
  }, [pathname])

  useEffect(() => {
    const openListener = (event: Event) => {
      const customEvent = event as CustomEvent<{ prompt?: string }>
      if (customEvent.detail?.prompt) {
        setInput(customEvent.detail.prompt)
      }
      setOpen(true)
    }

    window.addEventListener('nomad-ai-open', openListener)
    return () => window.removeEventListener('nomad-ai-open', openListener)
  }, [])

  const onOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen)
    if (!nextOpen && searchParams.get('assistant') === 'open') {
      router.replace(pathname)
    }
  }

  const sendQuery = async () => {
    if (!input.trim() || sending) return

    const rawQuery = input.trim()
    if (expandedForQuery !== rawQuery) {
      try {
        const preview = await apiClient.ambientAi.expand({
          query: rawQuery,
          trip_id: activeTripId || undefined,
          user_id: user?.id,
          screen,
        })
        setChips(preview.expanded_queries)
        setExpandedForQuery(rawQuery)
        setResponse(null)
        setError(null)
        return
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to expand query')
        setChips([])
        setExpandedForQuery(rawQuery)
      }
      return
    }

    setSending(true)
    setError(null)

    try {
      const payload = {
        query: rawQuery,
        trip_id: activeTripId || undefined,
        user_id: user?.id,
        screen,
      }
      const res = await apiClient.ambientAi.assist(payload)
      setResponse(res)
      setChips(res.expanded_queries)
      setExpandedForQuery(rawQuery)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to get assistant response')
    } finally {
      setSending(false)
    }
  }

  const removeChip = (chip: string) => {
    setChips((prev) => prev.filter((item) => item !== chip))
  }

  const runWithChip = (chip: string) => {
    setInput(chip)
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-30 rounded-full border border-[#d8c7af] bg-[#fffaf2] px-4 py-3 text-sm font-medium text-[#2d8a6e] shadow-lg transition hover:bg-[#f5f0e8] dark:border-[#5a3e20] dark:bg-[#2b1b0d] dark:text-[#8bd2bb] dark:hover:bg-[#352011]"
      >
        <span className="inline-flex items-center gap-2">
          <Sparkles className="h-4 w-4" /> Ambient AI
        </span>
      </button>

      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="bottom" className="h-[82vh] overflow-hidden rounded-t-2xl border-t border-[#d8c7af] bg-[#faf7f2] p-0 text-[#2c1a0e] shadow-2xl dark:border-[#5a3e20] dark:bg-[#1a1008] dark:text-[#f1e8dc]">
          <SheetHeader className="border-b border-[#d8c7af] bg-[#fffaf2] px-6 py-4 dark:border-[#5a3e20] dark:bg-[#2b1b0d]">
            <SheetTitle className="flex items-center gap-2 text-base text-[#2c1a0e] dark:text-[#fff7ea]">
              <MessageSquare className="h-4 w-4 text-[#2d8a6e] dark:text-[#8bd2bb]" />
              Nomad IQ Ambient Assistant
            </SheetTitle>
            <SheetDescription className="text-[#6b5a48] dark:text-[#dac8b3]">
              Context-aware assistance for this screen. No setup needed.
            </SheetDescription>
          </SheetHeader>

          <div className="grid h-[calc(82vh-86px)] grid-cols-1 gap-0 overflow-hidden lg:grid-cols-[1.55fr_1fr]">
            <div className="flex h-full flex-col overflow-hidden border-r border-[#d8c7af] bg-[#fffaf2] dark:border-[#5a3e20] dark:bg-[#241608]">
              <div className="flex items-center gap-2 p-4">
                <Input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Ask about your current trip context..."
                  disabled={sending}
                  className="border-[#d8c7af] bg-white text-[#2c1a0e] placeholder:text-[#8a7663] dark:border-[#5a3e20] dark:bg-[#1d1209] dark:text-[#f1e8dc] dark:placeholder:text-[#b9a896]"
                />
                <Button onClick={sendQuery} disabled={sending || !input.trim()} className="bg-[#2d8a6e] text-[#f4f8f5] hover:bg-[#256f59] dark:bg-[#8bd2bb] dark:text-[#1a1008] dark:hover:bg-[#9de0ca]">
                  {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Ask'}
                </Button>
              </div>

              {chips.length > 0 && (
                <div className="flex flex-wrap gap-2 border-t border-[#efe4d4] px-4 py-3 dark:border-[#3d280c]">
                  {chips.map((chip) => (
                    <div key={chip} className="inline-flex items-center rounded-full border border-[#d8c7af] bg-white pl-3 pr-1 py-1 text-xs text-[#2c1a0e] dark:border-[#5a3e20] dark:bg-[#2b1b0d] dark:text-[#f1e8dc]">
                      <button type="button" onClick={() => runWithChip(chip)} className="text-left text-[#2c1a0e] hover:text-[#2d8a6e] dark:text-[#f1e8dc] dark:hover:text-[#8bd2bb]">
                        {chip}
                      </button>
                      <button
                        type="button"
                        onClick={() => removeChip(chip)}
                        className="ml-1 rounded-full p-0.5 text-[#8a7663] hover:bg-[#f5f0e8] hover:text-[#2c1a0e] dark:text-[#b9a896] dark:hover:bg-[#352011] dark:hover:text-[#fff7ea]"
                        aria-label="Remove query chip"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex-1 overflow-y-auto px-4 pb-4 pt-2">
                {error && <div className="mb-3 rounded-lg border border-[#f0c2b4] bg-[#fff1eb] p-3 text-sm text-[#8f3b1f] dark:border-[#835645] dark:bg-[#352011] dark:text-[#f6c6b7]">{error}</div>}

                {!response && !sending && (
                  <div className="rounded-xl border border-dashed border-[#d8c7af] bg-[#f5f0e8] p-6 text-sm text-[#6b5a48] dark:border-[#5a3e20] dark:bg-[#2b1b0d] dark:text-[#dac8b3]">
                    Ask a question and Nomad IQ injects your active context automatically: screen, trip timing, budget, preferences, and disruption signals.
                  </div>
                )}

                {response && (
                  <div className="space-y-4">
                    <div className="rounded-xl border border-[#d8c7af] bg-[#fffdf8] p-4 text-sm leading-6 text-[#2c1a0e] whitespace-pre-wrap dark:border-[#5a3e20] dark:bg-[#1d1209] dark:text-[#f1e8dc]">
                      {response.answer}
                    </div>

                    {response.uncertainty_note && (
                      <div className="rounded-lg border border-[#e1c187] bg-[#fff6df] p-3 text-sm text-[#7a5516] dark:border-[#7f5b2a] dark:bg-[#352011] dark:text-[#f1d39c]">
                        {response.uncertainty_note}
                      </div>
                    )}

                    {response.proactive_cards.length > 0 && (
                      <div className="space-y-2">
                        {response.proactive_cards.map((card) => (
                          <div key={card.title} className="rounded-lg border border-[#cfe7dd] bg-[#effaf5] p-3 dark:border-[#355245] dark:bg-[#20140d]">
                            <p className="text-sm font-medium text-[#1f4e3d] dark:text-[#b9e6d6]">{card.title}</p>
                            <p className="mt-1 text-xs text-[#4e7264] dark:text-[#d2e7dd]">{card.detail}</p>
                            <p className="mt-2 text-xs font-medium text-[#2d8a6e] dark:text-[#8bd2bb]">{card.action_label}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="h-full overflow-y-auto bg-[#f5f0e8] p-4 text-[#2c1a0e] dark:bg-[#1a1008] dark:text-[#f1e8dc]">
              <p className="text-xs font-semibold uppercase tracking-wide text-[#6b5a48] dark:text-[#dac8b3]">Context Packet</p>
              {response?.context_packet ? (
                <div className="mt-3 space-y-3 text-sm text-[#2c1a0e] dark:text-[#f1e8dc]">
                  <div>
                    <p className="text-xs text-[#6b5a48] dark:text-[#dac8b3]">Screen</p>
                    <p className="font-medium">{response.context_packet.screen}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[#6b5a48] dark:text-[#dac8b3]">City</p>
                    <p className="font-medium">{response.context_packet.current_city || 'Unknown'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[#6b5a48] dark:text-[#dac8b3]">Budget Remaining</p>
                    <p className="font-medium">
                      {response.context_packet.remaining_budget != null
                        ? `${response.context_packet.budget_currency} ${response.context_packet.remaining_budget.toLocaleString()}`
                        : 'Not available'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[#6b5a48] dark:text-[#dac8b3]">Itinerary Snapshot</p>
                    <p className="font-medium">{response.context_packet.current_itinerary_summary || 'No active itinerary context'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[#6b5a48] dark:text-[#dac8b3]">Preferences</p>
                    <p className="font-medium">{response.context_packet.saved_preference_summary || 'No saved preference profile'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[#6b5a48] dark:text-[#dac8b3]">Active Disruptions</p>
                    {response.context_packet.active_disruptions.length > 0 ? (
                      <ul className="space-y-1">
                        {response.context_packet.active_disruptions.map((entry) => (
                          <li key={entry} className="rounded border border-[#e1c187] bg-[#fff6df] px-2 py-1 text-xs text-[#7a5516] dark:border-[#7f5b2a] dark:bg-[#352011] dark:text-[#f1d39c]">
                            {entry}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="font-medium">None detected</p>
                    )}
                  </div>

                  <div className="pt-2">
                    <Badge variant="secondary" className="bg-[#fffaf2] text-[#2c1a0e] dark:bg-[#2b1b0d] dark:text-[#f1e8dc]">Confidence {(response.confidence * 100).toFixed(0)}%</Badge>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-[#6b5a48] dark:text-[#dac8b3]">
                      {response.sources.map((source) => (
                        <Badge key={source} variant="outline" className="border-[#d8c7af] bg-white text-[#2c1a0e] dark:border-[#5a3e20] dark:bg-[#241608] dark:text-[#f1e8dc]">{source}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-3 text-sm text-[#6b5a48] dark:text-[#dac8b3]">Run a query to generate live context.</p>
              )}

              {trips.length > 0 && (
                <div className="mt-5 rounded-lg border border-[#d8c7af] bg-[#fffaf2] p-3 dark:border-[#5a3e20] dark:bg-[#241608]">
                  <p className="text-xs text-[#6b5a48] dark:text-[#dac8b3]">Bound trip</p>
                  <p className="text-sm font-medium">{activeTripId || 'Auto-selecting latest trip'}</p>
                </div>
              )}

              {response?.provenance?.memory_items.length ? (
                <div className="mt-5 rounded-lg border border-[#d8c7af] bg-[#fffaf2] p-3 dark:border-[#5a3e20] dark:bg-[#241608]">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[#6b5a48] dark:text-[#dac8b3]">Memory provenance</p>
                  <div className="mt-3 space-y-2">
                    {response.provenance.memory_items.map((item) => (
                      <details key={item.id} className="group rounded-lg border border-[#d8c7af] bg-[#f5f0e8] p-3 dark:border-[#5a3e20] dark:bg-[#1d1209]">
                        <summary className="cursor-pointer list-none text-sm font-medium text-[#2c1a0e] dark:text-[#fff7ea]">
                          <span className="inline-flex items-center gap-2">
                            <span>Memory {item.memory_type}</span>
                            <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-[#6b5a48] dark:bg-[#2b1b0d] dark:text-[#dac8b3]">
                              score {(item.score * 100).toFixed(0)}
                            </span>
                          </span>
                        </summary>
                        <div className="mt-3 space-y-2 text-xs text-[#6b5a48] dark:text-[#dac8b3]">
                          <p className="leading-5 text-[#2c1a0e] dark:text-[#f1e8dc]">{item.content}</p>
                          <div className="flex flex-wrap gap-1.5">
                            {item.matched_queries.map((query) => (
                              <Badge key={query} variant="secondary" className="bg-white text-[#2c1a0e] dark:bg-[#2b1b0d] dark:text-[#f1e8dc]">
                                {query}
                              </Badge>
                            ))}
                          </div>
                          <div className="grid grid-cols-2 gap-2 rounded-md bg-white p-2 text-[11px] text-[#6b5a48] dark:bg-[#2b1b0d] dark:text-[#dac8b3]">
                            <span>Semantic {(item.semantic_similarity * 100).toFixed(0)}%</span>
                            <span>Keyword {(item.keyword_match * 100).toFixed(0)}%</span>
                            <span>Recency {(item.recency * 100).toFixed(0)}%</span>
                            <span>Type {item.memory_type}</span>
                          </div>
                          <pre className="overflow-x-auto rounded-md bg-white p-2 text-[11px] leading-5 text-[#6b5a48] dark:bg-[#2b1b0d] dark:text-[#dac8b3]">
{JSON.stringify(item.metadata, null, 2)}
                          </pre>
                        </div>
                      </details>
                    ))}
                  </div>
                </div>
              ) : null}

              {response?.provenance?.tool_traces.length ? (
                <div className="mt-5 rounded-lg border border-[#d8c7af] bg-[#fffaf2] p-3 dark:border-[#5a3e20] dark:bg-[#241608]">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[#6b5a48] dark:text-[#dac8b3]">Tool traces</p>
                  <div className="mt-3 space-y-2">
                    {response.provenance.tool_traces.map((trace) => (
                      <details key={trace.tool_name} className="group rounded-lg border border-[#d8c7af] bg-[#f5f0e8] p-3 dark:border-[#5a3e20] dark:bg-[#1d1209]">
                        <summary className="cursor-pointer list-none text-sm font-medium text-[#2c1a0e] dark:text-[#fff7ea]">
                          <span className="inline-flex items-center gap-2">
                            <span>{trace.tool_name}</span>
                          </span>
                        </summary>
                        <div className="mt-3 space-y-2 text-xs text-[#6b5a48] dark:text-[#dac8b3]">
                          <p className="leading-5 text-[#2c1a0e] dark:text-[#f1e8dc]">{trace.summary}</p>
                          <div className="grid gap-2 md:grid-cols-2">
                            <div className="rounded-md bg-white p-2 dark:bg-[#2b1b0d]">
                              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#6b5a48] dark:text-[#dac8b3]">Inputs</p>
                              <pre className="mt-1 overflow-x-auto text-[11px] leading-5 text-[#6b5a48] dark:text-[#dac8b3]">
{JSON.stringify(trace.inputs, null, 2)}
                              </pre>
                            </div>
                            <div className="rounded-md bg-white p-2 dark:bg-[#2b1b0d]">
                              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#6b5a48] dark:text-[#dac8b3]">Outputs</p>
                              <pre className="mt-1 overflow-x-auto text-[11px] leading-5 text-[#6b5a48] dark:text-[#dac8b3]">
{JSON.stringify(trace.outputs, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </div>
                      </details>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </>
  )
}
