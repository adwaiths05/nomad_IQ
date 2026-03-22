'use client'

import { ProtectedRoute } from '@/components/protected-route'

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-slate-50">{children}</div>
    </ProtectedRoute>
  )
}
