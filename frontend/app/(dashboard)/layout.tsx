'use client'

import { ProtectedRoute } from '@/components/protected-route'
import { Sidebar } from '@/components/dashboard/sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  )
}
