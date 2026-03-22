'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/lib/context/auth-context'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Plane,
  MapPin,
  MessageCircle,
  BookOpen,
  LogOut,
  Menu,
  X,
  Home,
  User,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: Home },
  { href: '/dashboard/trips', label: 'My Trips', icon: Plane },
  { href: '/dashboard/itinerary', label: 'Itinerary', icon: MapPin },
  { href: '/dashboard/chat', label: 'AI Chat', icon: MessageCircle },
  { href: '/dashboard/guides', label: 'Travel Guides', icon: BookOpen },
]

export function Sidebar() {
  const router = useRouter()
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [isOpen, setIsOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard'
    }
    return pathname.startsWith(href)
  }

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-white border border-slate-200"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Sidebar */}
      <aside
        className={`${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 fixed lg:relative w-64 h-screen bg-white border-r border-slate-200 transition-transform duration-300 z-30 flex flex-col`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-slate-200 flex items-center space-x-2">
          <Plane className="w-8 h-8 text-blue-600" />
          <h1 className="text-xl font-bold text-slate-900">Nomadiq</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive(item.href) ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setIsOpen(false)}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {item.label}
                </Button>
              </Link>
            )
          })}
        </nav>

        {/* User menu */}
        <div className="p-4 border-t border-slate-200">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="w-full justify-start">
                <User className="w-4 h-4 mr-2" />
                <span className="truncate">{user?.username || 'User'}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="w-4 h-4 mr-2" />
                <span>Logout</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 lg:hidden z-20"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  )
}
