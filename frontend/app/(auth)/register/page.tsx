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
import { AlertCircle, Eye, EyeOff } from 'lucide-react'

const authCities = [
  { city: 'Mumbai', image: 'https://images.pexels.com/photos/2404048/pexels-photo-2404048.jpeg' },
  { city: 'Delhi', image: 'https://images.pexels.com/photos/7368048/pexels-photo-7368048.jpeg' },
  { city: 'Jaipur', image: 'https://images.pexels.com/photos/1450353/pexels-photo-1450353.jpeg' },
  { city: 'Bengaluru', image: 'https://images.pexels.com/photos/3888151/pexels-photo-3888151.jpeg' },
]

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error) return err.message
  if (err && typeof err === 'object' && 'message' in err) {
    const message = (err as { message?: unknown }).message
    if (typeof message === 'string' && message.trim().length > 0) {
      return message
    }
  }
  return fallback
}

export default function RegisterPage() {
  const router = useRouter()
  const { register } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [cityIndex, setCityIndex] = useState(0)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => {
      setCityIndex((prev) => (prev + 1) % authCities.length)
    }, 4500)
    return () => clearInterval(timer)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    setIsLoading(true)

    try {
      await register(username, email, password)
      localStorage.setItem('onboarding_completed', 'false')
      router.push('/onboarding/profile')
    } catch (err) {
      setError(getErrorMessage(err, 'Registration failed. Please try again.'))
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
          <p className="text-xs uppercase tracking-[0.2em] text-slate-300">Nomadiq Onboarding</p>
          <h2 className="text-4xl font-bold mt-2">Create your travel identity</h2>
          <p className="mt-3 text-slate-200">Currently featured: {authCities[cityIndex].city}</p>
        </div>
      </div>

      <div className="flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 to-slate-800">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-2xl">Create Account</CardTitle>
            <CardDescription>Join Nomadiq to start planning your adventures</CardDescription>
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
              <label htmlFor="username" className="text-sm font-medium">
                Username
              </label>
              <Input
                id="username"
                type="text"
                placeholder="johndoe"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

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
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <button
                  type="button"
                  className="text-xs text-slate-600 hover:text-slate-900 inline-flex items-center gap-1"
                  onClick={() => setShowPassword((prev) => !prev)}
                >
                  {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label htmlFor="confirmPassword" className="text-sm font-medium">
                  Confirm Password
                </label>
                <button
                  type="button"
                  className="text-xs text-slate-600 hover:text-slate-900 inline-flex items-center gap-1"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                >
                  {showConfirmPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                  {showConfirmPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Spinner className="mr-2 h-4 w-4" />
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </Button>
            </form>

            <div className="mt-4 text-center text-sm">
              Already have an account?{' '}
              <Link href="/login" className="text-blue-600 hover:underline">
                Sign in here
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
