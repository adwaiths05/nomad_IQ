'use client'

import { ProtectedRoute } from '@/components/protected-route'
import { Sidebar } from '@/components/dashboard/sidebar'
import { AmbientAiSheet } from '@/components/dashboard/ambient-ai-sheet'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <div className="post-auth-shell post-auth-dashboard flex h-screen">
        <Sidebar />
        <main className="post-auth-main flex-1 overflow-auto">
          {children}
        </main>
        <AmbientAiSheet />
      </div>
    </ProtectedRoute>
  )
}
