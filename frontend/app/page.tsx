'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Plane, Sparkles, MapPin, Users } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Plane className="w-8 h-8 text-blue-500" />
            <h1 className="text-2xl font-bold text-white">Nomadiq</h1>
          </div>
          <nav className="space-x-4">
            <Link href="/login">
              <Button variant="ghost" className="text-white hover:text-blue-400">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-blue-600 hover:bg-blue-700">Get Started</Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-white mb-6 text-balance">
            Plan Your Perfect Trip with AI
          </h2>
          <p className="text-xl text-slate-300 mb-8 text-balance max-w-2xl mx-auto">
            Nomadiq uses advanced AI to help you create personalized travel itineraries, discover hidden gems, and make the most of every adventure.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register">
              <Button className="bg-blue-600 hover:bg-blue-700 px-8 py-6 text-lg">
                Start Planning Now
              </Button>
            </Link>
            <Button variant="outline" className="px-8 py-6 text-lg border-slate-600 text-white hover:bg-slate-700">
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h3 className="text-3xl font-bold text-white mb-12 text-center">Why Choose Nomadiq?</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <Sparkles className="w-8 h-8 text-yellow-400 mb-2" />
              <CardTitle className="text-white">AI-Powered Planning</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300">
                Get personalized recommendations based on your preferences and travel style.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <MapPin className="w-8 h-8 text-red-400 mb-2" />
              <CardTitle className="text-white">Interactive Itineraries</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300">
                Create, customize, and organize your daily activities with ease.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <Users className="w-8 h-8 text-green-400 mb-2" />
              <CardTitle className="text-white">Chat Support</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300">
                Get instant answers and recommendations from our AI travel assistant.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <Plane className="w-8 h-8 text-blue-400 mb-2" />
              <CardTitle className="text-white">Expert Guides</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300">
                Access curated travel guides and insider tips for your destination.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <h3 className="text-3xl font-bold text-white mb-4">Ready to Explore the World?</h3>
        <p className="text-lg text-slate-300 mb-8">Join thousands of travelers using Nomadiq to plan amazing adventures.</p>
        <Link href="/register">
          <Button className="bg-blue-600 hover:bg-blue-700 px-8 py-6 text-lg">
            Create Your Free Account
          </Button>
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-700 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center text-slate-400">
          <p>&copy; 2024 Nomadiq. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
