'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/context/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'
import { AlertCircle } from 'lucide-react'

const authCities = [
  { city: 'Tokyo', image: 'https://images.pexels.com/photos/36290072/pexels-photo-36290072.jpeg' },
  { city: 'Lisbon', image: 'https://images.pexels.com/photos/5069524/pexels-photo-5069524.jpeg' },
  { city: 'Bali', image: 'https://images.pexels.com/photos/3913678/pexels-photo-3913678.jpeg' },
  { city: 'Seoul', image: 'https://images.pexels.com/photos/2067057/pexels-photo-2067057.jpeg' },
]

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [cityIndex, setCityIndex] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCityIndex((prev) => (prev + 1) % authCities.length)
    }, 4500)
    return () => clearInterval(timer)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await login(email, password)
      const onboardingDone = localStorage.getItem('onboarding_completed') === 'true'
      router.push(onboardingDone ? '/dashboard' : '/onboarding/profile')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-slate-950">
      <div className="hidden lg:flex relative overflow-hidden">
        <div
          className="absolute inset-0 transition-all duration-[1200ms] ease-out"
          style={{
            backgroundImage: `linear-gradient(120deg, rgba(2,6,23,0.75), rgba(2,6,23,0.2)), url('${authCities[cityIndex].image}')`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        />
        <div className="relative z-10 p-10 text-slate-100 self-end">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-300">Nomadiq Session</p>
          <h2 className="text-4xl font-bold mt-2">Continue your journey</h2>
          <p className="mt-3 text-slate-200">Currently featured: {authCities[cityIndex].city}</p>
        </div>
      </div>

      <div className="flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 to-slate-800">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-2xl">Welcome to Nomadiq</CardTitle>
            <CardDescription>Sign in to your account</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Spinner className="mr-2 h-4 w-4" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </Button>
            </form>

            <div className="mt-4 text-center text-sm">
              Don't have an account?{' '}
              <Link href="/register" className="text-blue-600 hover:underline">
                Register here
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
