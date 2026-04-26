'use client'

import { ProtectedRoute } from '@/components/protected-route'

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="post-auth-shell post-auth-onboarding min-h-screen">{children}</div>
    </ProtectedRoute>
  )
}
