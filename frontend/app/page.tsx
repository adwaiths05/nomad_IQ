'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { apiClient } from '../lib/api/client'

const slides = [
  { city: 'Tokyo', image: 'https://images.pexels.com/photos/36290072/pexels-photo-36290072.jpeg', accentColor: '#297bee', headlineColor: '#F2F0EA', subColor: '#9090b0' },
  { city: 'Lisbon', image: 'https://images.pexels.com/photos/5069524/pexels-photo-5069524.jpeg', accentColor: '#FFB347', headlineColor: '#FDF6E3', subColor: '#b08050' },
  { city: 'Bali', image: 'https://images.pexels.com/photos/3913678/pexels-photo-3913678.jpeg', accentColor: '#7eda8a', headlineColor: '#F0F5F0', subColor: '#608060' },
  { city: 'Amalfi Coast', image: 'https://images.pexels.com/photos/358223/pexels-photo-358223.jpeg', accentColor: '#36e7cc', headlineColor: '#EDF4FB', subColor: '#5080a0' },
  { city: 'Kyoto', image: 'https://images.pexels.com/photos/6793716/pexels-photo-6793716.jpeg', accentColor: '#c8e890', headlineColor: '#F5F5EE', subColor: '#708058' },
  { city: 'Santorini', image: 'https://images.pexels.com/photos/221532/pexels-photo-221532.jpeg', accentColor: '#88aaff', headlineColor: '#FFFFFF', subColor: '#5068b0' },
  { city: 'New York', image: 'https://images.pexels.com/photos/747101/pexels-photo-747101.jpeg', accentColor: '#1847ef', headlineColor: '#F8F8F8', subColor: '#1e3a5f' },
  { city: 'Seoul', image: 'https://images.pexels.com/photos/2067057/pexels-photo-2067057.jpeg', accentColor: '#e080ff', headlineColor: '#F5EEFF', subColor: '#8058a0' },
  { city: 'The Dolomites', image: 'https://plus.unsplash.com/premium_photo-1724424666831-98f263e2ea4a?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', accentColor: '#90d0f0', headlineColor: '#EEF2F8', subColor: '#6080a0' },
  { city: 'Banff National Park', image: 'https://images.unsplash.com/photo-1503614472-8c93d56e92ce?q=80&w=1111&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', accentColor: '#50e0c8', headlineColor: '#E8F5F2', subColor: '#408070' },
]

const typewriterPhrases = [
  'Surprise me in Tokyo for 5 days under €1,500',
  'Plan a weekend in Lisbon with great food',
  'Austin for SXSW — 4 days, budget €800',
  'Somewhere warm, 7 days, eco-friendly',
]


const integrationCards = [
  {
    provider: 'mcp-travel',
    description: 'Flights + city spots + nearby spots + transit duration in one travel boundary',
    endpoint: 'POST /integrations/transport/search-flights',
  },
  {
    provider: 'backend-weather',
    description: 'Objective wellness context (AQI, weather, heat index) via OpenWeather',
    endpoint: 'POST /integrations/wellness/objective-signals',
  },
  {
    provider: 'backend-events',
    description: 'Local event intelligence via Ticketmaster + Eventbrite + festival fallback',
    endpoint: 'POST /integrations/events/search',
  },
  {
    provider: 'backend-finance',
    description: 'Exchange rates and city cost baselines with deterministic fallback',
    endpoint: 'POST /integrations/finance/exchange-rates',
  },
  {
    provider: 'backend-safety-secondary',
    description: 'OpenWeather core safety (AQI/UV/heat) + context signals (events/time/location type)',
    endpoint: 'POST /integrations/safety/score',
  },
  {
    provider: 'backend-environment',
    description: 'Climatiq route emissions with deterministic fallback',
    endpoint: 'POST /integrations/environment/route-emissions',
  },
  {
    provider: 'mcp-rag',
    description: 'Long-term and short-term pgvector memory search',
    endpoint: 'POST /integrations/rag/search-long-term',
  },
]

export default function HomePage() {
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false)
  const [isAiDemoInView, setIsAiDemoInView] = useState(false)
  const [isStatsInView, setIsStatsInView] = useState(false)
  const [isEnvelopeOpened, setIsEnvelopeOpened] = useState(false)
  const [budgetValue, setBudgetValue] = useState(1240)
  const [scrollY, setScrollY] = useState(0)
  const [navbarScroll, setNavbarScroll] = useState(false)
  const [inputFocused, setInputFocused] = useState(false)
  const [typewriterText, setTypewriterText] = useState('')
  const [typewriterIndex, setTypewriterIndex] = useState(0)
  const [activePillar, setActivePillar] = useState<number | null>(null)
  const [tripcastFlipped, setTripcastFlipped] = useState<number | null>(null)
  const [tripcastIndex, setTripcastIndex] = useState(0)
  const [scrollProgress, setScrollProgress] = useState(0)
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 })
  const [budgetText, setBudgetText] = useState('Looking for budget-friendly hidden gems...')
  const [activeCityIndex, setActiveCityIndex] = useState(0)
  const [dissolveKey, setDissolveKey] = useState(0)
  const [accentColor, setAccentColor] = useState(slides[0].accentColor)
  const [headlineColor, setHeadlineColor] = useState(slides[0].headlineColor)
  const [subColor, setSubColor] = useState(slides[0].subColor)
  const [isHeroHovered, setIsHeroHovered] = useState(false)
  const [progressWidth, setProgressWidth] = useState(0)
  const [selectedDot, setSelectedDot] = useState(0)
  const [cityNameBlur, setCityNameBlur] = useState(false)
  const [discoveryLoading, setDiscoveryLoading] = useState(false)
  const [discoveryError, setDiscoveryError] = useState<string | null>(null)
  const [discoveryItems, setDiscoveryItems] = useState<Array<Record<string, unknown>>>([])
  const [discoveryCity, setDiscoveryCity] = useState(slides[0].city)
  const [discoveryStartDate, setDiscoveryStartDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [discoveryEndDate, setDiscoveryEndDate] = useState(() => {
    const next = new Date()
    next.setDate(next.getDate() + 2)
    return next.toISOString().slice(0, 10)
  })
  const [discoveryTimeOfDay, setDiscoveryTimeOfDay] = useState('evening')
  const [discoveryLocationType, setDiscoveryLocationType] = useState('tourist')

  const [stats, setStats] = useState({
    trips: 0,
    budget: 0,
    co2: 0,
    apis: 0,
  })

  const aiDemoRef = useRef<HTMLElement | null>(null)
  const statsRef = useRef<HTMLElement | null>(null)
  const heroRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    const aiObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsAiDemoInView(true)
            entry.target.classList.add('in-view')
          }
        })
      },
      { threshold: 0.1 }
    )

    const sectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view')
          }
        })
      },
      { threshold: 0.1 }
    )

    if (aiDemoRef.current) {
      aiObserver.observe(aiDemoRef.current)
    }

    document.querySelectorAll('section').forEach((section) => {
      sectionObserver.observe(section)
    })

    return () => {
      aiObserver.disconnect()
      sectionObserver.disconnect()
    }
  }, [])

  const loadDiscovery = async (payloadOverride?: Record<string, unknown>) => {
    setDiscoveryLoading(true)
    setDiscoveryError(null)
    try {
      const payload = {
        city: discoveryCity,
        start_date: discoveryStartDate,
        end_date: discoveryEndDate,
        budget_cap: budgetValue,
        time_of_day: discoveryTimeOfDay,
        location_type: discoveryLocationType,
        max_results: 3,
        ...(payloadOverride || {}),
      }

      const response = await apiClient.integrations.eventsDiscover(payload)
      const rows = response && typeof response === 'object' ? (response as Record<string, unknown>).recommendations : null
      setDiscoveryItems(Array.isArray(rows) ? (rows as Array<Record<string, unknown>>) : [])
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not load discovery suggestions.'
      setDiscoveryError(message)
      setDiscoveryItems([])
    } finally {
      setDiscoveryLoading(false)
    }
  }

  useEffect(() => {
    setDiscoveryCity(slides[activeCityIndex].city)
  }, [activeCityIndex])

  useEffect(() => {
    loadDiscovery()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const renderDiscoveryControls = () => (
    <>
      <label className="discovery-label" htmlFor="discovery-city">City</label>
      <input
        id="discovery-city"
        className="discovery-input"
        type="text"
        value={discoveryCity}
        onChange={(event) => setDiscoveryCity(event.target.value)}
        placeholder="Tokyo"
      />

      <div className="discovery-control-row">
        <div>
          <label className="discovery-label" htmlFor="discovery-start">Start</label>
          <input
            id="discovery-start"
            className="discovery-input"
            type="date"
            value={discoveryStartDate}
            onChange={(event) => setDiscoveryStartDate(event.target.value)}
          />
        </div>
        <div>
          <label className="discovery-label" htmlFor="discovery-end">End</label>
          <input
            id="discovery-end"
            className="discovery-input"
            type="date"
            value={discoveryEndDate}
            onChange={(event) => setDiscoveryEndDate(event.target.value)}
          />
        </div>
      </div>

      <label className="discovery-label" htmlFor="discovery-budget">Budget cap: €{budgetValue}</label>
      <input
        id="discovery-budget"
        className="discovery-range"
        type="range"
        min={500}
        max={3000}
        step={50}
        value={budgetValue}
        onChange={(event) => setBudgetValue(Number(event.target.value))}
      />

      <div className="discovery-control-row">
        <div>
          <label className="discovery-label" htmlFor="discovery-time">Time</label>
          <select
            id="discovery-time"
            className="discovery-input"
            value={discoveryTimeOfDay}
            onChange={(event) => setDiscoveryTimeOfDay(event.target.value)}
          >
            <option value="morning">Morning</option>
            <option value="afternoon">Afternoon</option>
            <option value="evening">Evening</option>
            <option value="night">Night</option>
          </select>
        </div>
        <div>
          <label className="discovery-label" htmlFor="discovery-location">Area type</label>
          <select
            id="discovery-location"
            className="discovery-input"
            value={discoveryLocationType}
            onChange={(event) => setDiscoveryLocationType(event.target.value)}
          >
            <option value="tourist">Tourist</option>
            <option value="commercial">Commercial</option>
            <option value="residential">Residential</option>
            <option value="isolated">Isolated</option>
            <option value="transit_hub">Transit hub</option>
          </select>
        </div>
      </div>

      <button className="teal-button discovery-run" type="button" onClick={() => loadDiscovery()}>
        Run Discovery
      </button>
    </>
  )

  useEffect(() => {
    const statsObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsStatsInView(true)
          }
        })
      },
      { threshold: 0.35 }
    )

    if (statsRef.current) {
      statsObserver.observe(statsRef.current)
    }

    return () => {
      statsObserver.disconnect()
    }
  }, [])

  useEffect(() => {
    if (!isStatsInView) {
      return
    }

    const targets = {
      trips: 23400,
      budget: 4200000,
      co2: 18200,
      apis: 8,
    }

    const durations = { trips: 2200, budget: 1800, co2: 2000, apis: 1200 }
    const startedAt = performance.now()

    const updateCount = (now: number) => {
      const elapsed = now - startedAt

      setStats({
        trips: elapsed >= durations.trips ? targets.trips : Math.floor((targets.trips * Math.min(elapsed / durations.trips, 1)) * (1 - Math.pow(1 - Math.min(elapsed / durations.trips, 1), 3))),
        budget: elapsed >= durations.budget ? targets.budget : Math.floor((targets.budget * Math.min(elapsed / durations.budget, 1)) * (1 - Math.pow(1 - Math.min(elapsed / durations.budget, 1), 3))),
        co2: elapsed >= durations.co2 ? targets.co2 : Math.floor((targets.co2 * Math.min(elapsed / durations.co2, 1)) * (1 - Math.pow(1 - Math.min(elapsed / durations.co2, 1), 3))),
        apis: elapsed >= durations.apis ? targets.apis : Math.floor((targets.apis * Math.min(elapsed / durations.apis, 1)) * (1 - Math.pow(1 - Math.min(elapsed / durations.apis, 1), 3))),
      })

      if (elapsed < Math.max(...Object.values(durations))) {
        requestAnimationFrame(updateCount)
      }
    }

    requestAnimationFrame(updateCount)
  }, [isStatsInView])

  useEffect(() => {
    const handleScroll = () => {
      const y = window.scrollY
      setScrollY(y)
      setNavbarScroll(y > 80)

      if (heroRef.current) {
        const heroBottom = heroRef.current.offsetHeight
        if (y < heroBottom) {
          heroRef.current.style.backgroundPositionY = `${y * 0.4}px`
        }
      }

      const docHeight = document.documentElement.scrollHeight
      const winHeight = window.innerHeight
      const pct = Math.min((y / (docHeight - winHeight)) * 100, 100)
      setScrollProgress(pct)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    if (!inputFocused) return

    let charIndex = 0
    let phraseIndex = typewriterIndex
    let isDeleting = false
    const currentPhrase = typewriterPhrases[phraseIndex]

    const typeChar = () => {
      if (!isDeleting) {
        if (charIndex < currentPhrase.length) {
          setTypewriterText(currentPhrase.substring(0, charIndex + 1))
          charIndex++
          setTimeout(typeChar, 80)
        } else {
          setTimeout(() => {
            isDeleting = true
            typeChar()
          }, 2000)
        }
      } else {
        if (charIndex > 0) {
          setTypewriterText(currentPhrase.substring(0, charIndex - 1))
          charIndex--
          setTimeout(typeChar, 40)
        } else {
          setTypewriterIndex((prev) => (prev + 1) % typewriterPhrases.length)
          isDeleting = false
          setTimeout(typeChar, 500)
        }
      }
    }

    setTimeout(typeChar, 100)
  }, [inputFocused, typewriterIndex])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setCursorPos({ x: e.clientX, y: e.clientY })
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      setTripcastIndex((prev) => (prev + 1) % 3)
    }, 4000)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const slideDuration = 6000
    const progressInterval = setInterval(() => {
      setProgressWidth((prev) => {
        if (prev >= 100) return 0
        return prev + (100 / (slideDuration / 50))
      })
    }, 50)

    const cityInterval = setInterval(() => {
      setActiveCityIndex((prev) => {
        const nextIndex = (prev + 1) % slides.length
        setCityNameBlur(true)
        setTimeout(() => setCityNameBlur(false), 300)
        setAccentColor(slides[nextIndex].accentColor)
        setHeadlineColor(slides[nextIndex].headlineColor)
        setSubColor(slides[nextIndex].subColor)
        setSelectedDot(nextIndex)
        setDissolveKey((key) => key + 1)
        return nextIndex
      })
      setProgressWidth(0)
    }, slideDuration)

    return () => {
      clearInterval(progressInterval)
      clearInterval(cityInterval)
    }
  }, [])

  const handleDotClick = (index: number) => {
    setActiveCityIndex(index)
    setAccentColor(slides[index].accentColor)
    setHeadlineColor(slides[index].headlineColor)
    setSubColor(slides[index].subColor)
    setSelectedDot(index)
    setProgressWidth(0)
    setDissolveKey((key) => key + 1)
  }

  const updateBudgetText = (value: number) => {
    if (value <= 500)
      setBudgetText('Looking for budget-friendly hidden gems...')
    else if (value <= 1000)
      setBudgetText('Finding the sweet spot — quality without excess...')
    else if (value <= 2000)
      setBudgetText('Curating a premium experience...')
    else setBudgetText('No limits. Here\'s somewhere extraordinary...')
  }

  return (
    <main className="landing-page">
      <section
        ref={heroRef}
        className="landing-hero"
        data-dissolve-key={dissolveKey}
        style={{
          backgroundImage: `url('${slides[activeCityIndex].image}')`
        }}
        onMouseEnter={() => setIsHeroHovered(true)}
        onMouseLeave={() => setIsHeroHovered(false)}
      >
        <div className="progress-bar" style={{ width: `${progressWidth}%`, backgroundColor: accentColor }} />

        <header className={`landing-nav ${navbarScroll ? 'scrolled' : ''}`}>
          <div className="landing-logo">Nomadiq</div>
          <Link className="ghost-link" href="/login">
            Sign in
          </Link>
        </header>

        <div className="hero-inner">
          <div className="hero-content-box">
            <p className="hero-eyebrow" style={{ color: '#ffffff', transition: 'color 1.2s ease' }}>AI-powered travel intelligence</p>
            <h1 className="hero-title" style={{ color: headlineColor, transition: 'color 1.2s ease' }}>
              Your next trip to{' '}
              <span 
                className={`city-accent ${cityNameBlur ? 'blurred' : ''}`}
                style={{ color: accentColor, transition: 'color 1.2s ease' }}
                aria-label="Rotating city name"
                aria-live="polite"
              >
                [{slides[activeCityIndex].city}]
              </span>
              , planned by intelligence.
            </h1>
            <p className="hero-subtitle" style={{ color: headlineColor, transition: 'color 1.2s ease' }}>
              One sentence. Real-time data. A full itinerary - optimised for budget,
              eco-impact, and what actually matters to you.
            </p>
          </div>

          <div className="hero-input-group">
            <div className="input-wrapper">
              <input
                className={`hero-input ${inputFocused ? 'focused' : ''}`}
                type="text"
                placeholder={typewriterText || 'Try: "Surprise me in Tokyo for 5 days under €1,500"'}
                aria-label="Trip prompt"
                onFocus={() => setInputFocused(true)}
                onBlur={() => setInputFocused(false)}
              />
              <div className="input-glow" />
            </div>
            <button
              className="teal-button"
              type="button"
              onClick={() => setIsSignupModalOpen(true)}
              style={{ 
                background: `linear-gradient(130deg, ${accentColor}, ${accentColor})`,
                transition: 'background 1.2s ease'
              }}
            >
              Plan my trip →
            </button>
          </div>

          <div className={`pill-row suggestion-pills-row ${inputFocused ? 'visible' : ''}`} role="list" aria-label="Prompt suggestions">
            <button className="suggestion-pill" type="button" style={{ '--delay': '0ms' } as React.CSSProperties}>
              🗽 Tokyo · 5 days
            </button>
            <button className="suggestion-pill" type="button" style={{ '--delay': '80ms' } as React.CSSProperties}>
              🏖 Amalfi · weekend
            </button>
            <button className="suggestion-pill" type="button" style={{ '--delay': '160ms' } as React.CSSProperties}>
              🎵 Austin SXSW
            </button>
          </div>

          <div className="slide-dots" role="tablist" aria-label="Slide indicators">
            {slides.map((_, index) => (
              <button
                key={index}
                className={`slide-dot ${selectedDot === index ? 'active' : ''}`}
                onClick={() => handleDotClick(index)}
                role="tab"
                aria-selected={selectedDot === index}
                aria-label={`Go to slide ${index + 1}: ${slides[index].city}`}
                style={selectedDot === index ? { backgroundColor: accentColor } : {}}
              />
            ))}
          </div>
        </div>

        <div className="scroll-indicator" aria-hidden="true">
          <span className="chevron" />
        </div>
      </section>

      <section ref={aiDemoRef} className="ai-moment-section">
        <div className="section-shell">
          <p className="section-label">How it works</p>
          <h2 className="section-title">Watch the intelligence work.</h2>
          <p className="section-copy">
            Nomadiq doesn&apos;t just generate a list. It fetches live weather,
            checks event schedules, evaluates crowd scores, and explains every
            decision - in real time.
          </p>

          <div className={`browser-mockup ${isAiDemoInView ? 'play' : ''}`}>
            <div className="browser-topbar">
              <span />
              <span />
              <span />
            </div>

            <div className="demo-budget-row">
              <div className="demo-budget-track">
                <div className="demo-budget-live" />
              </div>
            </div>

            <div className="demo-cards">
              <article className="demo-card">
                <div className="demo-thumb skeleton-block" />
                <div className="demo-card-content">
                  <h3>Meiji Shrine Gate</h3>
                  <p>08:30 - 09:45</p>
                  <div className="confidence-row">
                    <div className="confidence-ring" aria-hidden="true">
                      <svg viewBox="0 0 100 100">
                        <circle className="ring-track" cx="50" cy="50" r="45" />
                        <circle className="ring-value" cx="50" cy="50" r="45" />
                      </svg>
                    </div>
                    <span>87% confidence - enriched via mcp-travel + objective wellness signals</span>
                  </div>
                  <span className="why-chip">
                    Chosen for low crowd score (2.1) before 10am and proximity to
                    your Day 1 anchor
                  </span>
                </div>
              </article>

              <article className="demo-card">
                <div className="demo-thumb skeleton-block" />
                <div className="demo-card-content">
                  <h3>Shibuya Crossing Viewpoint</h3>
                  <p>10:15 - 11:00</p>
                </div>
              </article>

              <article className="demo-card">
                <div className="demo-thumb skeleton-block" />
                <div className="demo-card-content">
                  <h3>Nezu Museum Garden</h3>
                  <p>11:30 - 12:40</p>
                </div>
              </article>
            </div>
          </div>


        </div>
      </section>

      <section className="pillars-section">
        <div className="section-shell">
          <div className="pillars-grid">
            <article className="pillar-card" onMouseEnter={() => setActivePillar(0)} onMouseLeave={() => setActivePillar(null)}>
              <div className={`pillar-visual planning-visual ${activePillar === 0 ? 'active' : ''}`}>
                <p className="typing-line">5 days in Kyoto</p>
                <div className="planning-skeleton" />
                <div className="plan-mini-cards">
                  <span>Fushimi Inari</span>
                  <span>Gion Walk</span>
                  <span>Arashiyama</span>
                </div>
              </div>

              <h3>Plans that think ahead.</h3>
              <p>
                Natural language in. A fully optimised, scored, explainable
                itinerary out - pulling live data from mcp-travel and backend
                adapters for events, weather, and wellness signals.
              </p>
            </article>

            <article className="pillar-card" onMouseEnter={() => setActivePillar(1)} onMouseLeave={() => setActivePillar(null)}>
              <div className={`pillar-visual budget-visual ${activePillar === 1 ? 'active' : ''}`}>
                <div className="budget-meter">
                  <div className="budget-meter-fill" />
                </div>
                <p className="budget-ticker">€1,204 / €1,500</p>
                <div className="alt-card">Cheaper alternatives available nearby</div>
              </div>

              <h3>Money that never runs out of plan.</h3>
              <p>
                Real-time spend tracking against Numbeo cost baselines. When
                budget pressure hits 80%, Nomadiq automatically suggests
                alternatives - before you feel it.
              </p>
            </article>

            <article className="pillar-card" onMouseEnter={() => setActivePillar(2)} onMouseLeave={() => setActivePillar(null)}>
              <div className={`pillar-visual eco-visual ${activePillar === 2 ? 'active' : ''}`}>
                <div className="route-grid">
                  <div className="route-option">12.4kg CO2</div>
                  <div className="route-option eco-choice">8.1kg CO2</div>
                  <div className="route-option">15.2kg CO2</div>
                </div>
                <p className="tree-counter">= 3 trees saved this trip.</p>
              </div>

              <h3>Travel lighter. Literally.</h3>
              <p>
                Every route is scored for carbon emissions via Climatiq. Nomadiq
                shows you the tradeoff between time, cost, and CO2 - then lets you
                choose what matters most.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="discovery-section">
        <div className="section-shell">
          <p className="section-label">Discovery Layer</p>
          <h2 className="section-title">Local Event Intelligence in action.</h2>
          <p className="section-copy">
            This section calls <strong>/integrations/events/discover</strong> and fuses Ticketmaster + Eventbrite + places + cost + weather/context into ranked suggestions.
          </p>

          <div className="discovery-mobile-controls">
            <details>
              <summary>Adjust city, dates, budget, and context</summary>
              <div className="discovery-controls-inner">{renderDiscoveryControls()}</div>
            </details>
          </div>

          <div className="discovery-layout">
            <aside className="discovery-controls desktop-only">
              <p className="section-label">Inputs</p>
              <h3>Tune the decision engine</h3>
              <p>Set constraints, then run discovery to rank local event + place combinations.</p>
              <div className="discovery-controls-inner">{renderDiscoveryControls()}</div>
            </aside>

            <div className="discovery-results">
              {discoveryLoading && <p className="section-copy">Loading discovery recommendations...</p>}
              {!discoveryLoading && discoveryError && <p className="section-copy">Discovery unavailable: {discoveryError}</p>}

              {!discoveryLoading && !discoveryError && discoveryItems.length > 0 && (
                <div className="pillars-grid discovery-cards">
                  {discoveryItems.map((item, index) => {
                    const eventObj = (item.event as Record<string, unknown> | undefined) || {}
                    const placeObj = (item.place as Record<string, unknown> | undefined) || {}
                    const eventName = String(eventObj.name || 'Local event')
                    const placeName = String(placeObj.name || 'Nearby cafe')
                    const cost = Number(item.estimated_cost ?? 0)
                    const transit = Number(item.estimated_transit_minutes ?? 0)
                    const crowd = String(item.crowd_level || 'medium')
                    const score = Number(item.discovery_score ?? 0)

                    return (
                      <article className="pillar-card" key={`discovery-${index}`}>
                        <div className="pillar-visual planning-visual active">
                          <p className="typing-line">{eventName}</p>
                          <div className="planning-skeleton" />
                          <div className="plan-mini-cards">
                            <span>{placeName}</span>
                            <span>₹{cost.toFixed(0)} est.</span>
                            <span>{transit} min away</span>
                          </div>
                        </div>

                        <h3>{placeName} + {eventName}</h3>
                        <p>
                          {`Coffee + local event (₹${cost.toFixed(0)}, ${transit} min away, ${crowd} crowd)`}
                        </p>
                        <p className="recruiter-note">Discovery score: {score.toFixed(1)} / 100</p>
                      </article>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="autopilot-section">
        <div className="section-shell autopilot-grid">
          <div className="autopilot-controls">
            <h2 className="section-title">No idea where to go? Perfect.</h2>
            <p className="section-copy">
              Set your budget and dates. Nomadiq picks the destination, plans the
              trip, and delivers it sealed. Open it when you&apos;re ready.
            </p>

            <div className="envelope-shell preview-envelope" aria-hidden="true">
              <div className="envelope-letter">Sealed surprise</div>
            </div>

            <label className="control-label" htmlFor="budget-slider">
              Budget: €{budgetValue} / €3,000
            </label>
            <input
              id="budget-slider"
              type="range"
              min={500}
              max={3000}
              value={budgetValue}
              onChange={(event) => {
                const val = Number(event.target.value)
                setBudgetValue(val)
                updateBudgetText(val)
              }}
            />
            <p className="budget-feedback-text">{budgetText}</p>

            <div className="date-row">
              <input type="date" aria-label="Start date" />
              <input type="date" aria-label="End date" />
            </div>

            <button
              className="teal-button"
              type="button"
              onClick={() => setIsEnvelopeOpened(true)}
            >
              Generate my surprise trip -&gt;
            </button>
          </div>

          <div className="autopilot-reveal">
            <div className={`envelope-shell ${isEnvelopeOpened ? 'opened' : ''}`}>
              <div className="envelope-letter">
                <h3>Your trip to Porto</h3>
                <p>
                  4 days · €{budgetValue} estimated · Safety 8.4 · 18°C clear
                </p>
                <div className="reveal-cards">
                  <span>Day 1: Ribeira + sunset cruise</span>
                  <span>Day 2: Douro valley rail route</span>
                  <span>Day 3: Foz coast + live fado</span>
                </div>
              </div>
            </div>


            <p className="recruiter-note">
              Multi-API orchestration in a single action - 4 endpoints firing
              simultaneously, composed into one reveal.
            </p>
          </div>
        </div>
      </section>

      <section className="tripcast-section">
        <div className="section-shell">
          <p className="section-label">Tripcast</p>
          <h2 className="section-title">Your trip, briefed 48 hours before you leave.</h2>
          <p className="section-copy">
            Nomadiq assembles a cinematic pre-trip brief - weather, safety,
            events, and budget readiness - delivered as a shareable story. One
            swipe. Full picture.
          </p>

          <div className="tripcast-carousel">
            {[
              {
                image: 'https://images.unsplash.com/photo-1480796927426-f609979314bd?auto=format&fit=crop&w=900&q=80',
                title: 'Tokyo - Day 1',
                subtitle: 'Clear skies, 22°C · Low humidity',
              },
              {
                image: 'https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?auto=format&fit=crop&w=900&q=80',
                title: 'Shibuya area',
                subtitle: 'Safety 9.1 · Low crowd density · Arrive 8:30am',
              },
              {
                image: 'https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=900&q=80',
                title: 'Fuji Rock Festival - Day 3',
                subtitle: '¥12,000 · 2.4km from hotel',
              },
            ].map((card, idx) => (
              <article
                key={idx}
                className={`tripcast-card ${idx === 0 ? 'rotate-left' : idx === 2 ? 'rotate-right' : ''} ${tripcastIndex === idx ? 'active' : ''}`}
                style={{ backgroundImage: `url('${card.image}')` }}
                onClick={() => setTripcastFlipped(tripcastFlipped === idx ? null : idx)}
              >
                <div className="tripcast-overlay">
                  <h3>{card.title}</h3>
                  <p>{card.subtitle}</p>
                </div>
              </article>
            ))}
          </div>

          <button className="ghost-link card-ghost" type="button">
            Share your Tripcast
          </button>
        </div>
      </section>

      <section className="integrations-section">
        <div className="section-shell">
          <div className="marquee">
            <div className="marquee-track">
              {[...integrationCards, ...integrationCards].map((item, index) => (
                <article className="integration-card" key={`${item.provider}-${index}`}>
                  <h3>{item.provider}</h3>
                  <p>{item.description}</p>
                  <span>{item.endpoint}</span>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section ref={statsRef} className="stats-section">
        <div className="section-shell stats-grid">
          <article>
            <h3>{stats.trips.toLocaleString()}+</h3>
            <p>trips planned</p>
            <div dangerouslySetInnerHTML={{ __html: '<!-- via POST /plan-trip -->' }} />
          </article>
          <article>
            <h3>EUR{(stats.budget / 1000000).toFixed(1)}M</h3>
            <p>in budget saved</p>
            <div dangerouslySetInnerHTML={{ __html: '<!-- via /budget/optimize -->' }} />
          </article>
          <article>
            <h3>{stats.co2.toLocaleString()} kg</h3>
            <p>CO2 avoided</p>
            <div dangerouslySetInnerHTML={{ __html: '<!-- via /integrations/environment/route-emissions -->' }} />
          </article>
          <article>
            <h3>{stats.apis} live APIs</h3>
            <p>orchestrated in real time</p>
            <div
              dangerouslySetInnerHTML={{
                __html: '<!-- via MCP integration layer -->',
              }}
            />
          </article>
        </div>
      </section>

      <section
        className="final-cta"
      >
        <video
          className="final-cta-video"
          autoPlay
          loop
          muted
          playsInline
          src="https://www.pexels.com/download/video/33847568/"
        />
        <div className="final-cta-overlay" />
        <div className="final-inner">
          <h2 className="hero-title">Your next adventure starts with one sentence.</h2>
          <button
            className="teal-button"
            type="button"
            onClick={() => setIsSignupModalOpen(true)}
          >
            Start planning free -&gt;
          </button>
          <a className="ghost-link" href="https://github.com/adwaiths05/nomad_IQ" target="_blank" rel="noreferrer">
            View source on GitHub -&gt;
          </a>

          <div className="pill-row final-pills">
            <span className="suggestion-pill">No credit card</span>
            <span className="suggestion-pill">Live data, always</span>
            <span className="suggestion-pill">Open source backend</span>
          </div>

          <p className="stack-footnote">
            Built with Claude - FastAPI - PostgreSQL - MCP - 8 live integrations
          </p>
        </div>
      </section>

      {isSignupModalOpen && (
        <div
          className="signup-modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-label="Create your account"
        >
          <div className="signup-modal">
            <h2>Create your account</h2>
            <p>One minute setup. Start planning immediately.</p>
            <input type="email" placeholder="Email" aria-label="Email" />
            <input type="password" placeholder="Password" aria-label="Password" />
            <div className="modal-actions">
              <button
                className="ghost-link"
                type="button"
                onClick={() => setIsSignupModalOpen(false)}
              >
                Maybe later
              </button>
              <Link className="teal-button" href="/register">
                Continue
              </Link>
            </div>
          </div>
        </div>
      )}

      <div className="scroll-progress-bar" style={{ width: `${scrollProgress}%` }} aria-hidden="true" />
      <div className="cursor-glow" style={{ left: `${cursorPos.x}px`, top: `${cursorPos.y}px` }} aria-hidden="true" />
    </main>
  )
}
