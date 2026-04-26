'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { useTheme } from 'next-themes'
import { useAuth } from '@/lib/context/auth-context'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Plane,
  MapPin,
  Compass,
  Stethoscope,
  Film,
  BookOpen,
  LogOut,
  Menu,
  X,
  Home,
  User,
  Moon,
  Sun,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: Home },
  { href: '/plan', label: 'Trip Planner', icon: Compass },
  { href: '/trips', label: 'Trips', icon: Plane },
  { href: '/places', label: 'Place Discovery', icon: MapPin },
  { href: '/trips/demo-trip/health', label: 'Trip Health', icon: Stethoscope },
  { href: '/trips/demo-trip/tripcast', label: 'Tripcast', icon: Film },
  { href: '/profile', label: 'Profile + Insights', icon: User },
  { href: '/dashboard/guides', label: 'Travel Guides', icon: BookOpen },
]

export function Sidebar() {
  const router = useRouter()
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
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

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-[var(--auth-panel)] border border-[var(--auth-border)] text-[var(--auth-text)]"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Sidebar */}
      <aside
        className={`${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } post-auth-sidebar lg:translate-x-0 fixed lg:relative w-64 h-screen transition-transform duration-300 z-30 flex flex-col`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-[var(--auth-border)] flex items-center space-x-2">
          <Plane className="w-8 h-8 text-[var(--auth-teal)]" />
          <h1 className="text-xl font-bold text-[var(--auth-heading)]">Nomadiq</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant="ghost"
                  className={`w-full justify-start ${isActive(item.href) ? 'post-auth-nav-active' : 'post-auth-nav-item'}`}
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
        <div className="p-4 border-t border-[var(--auth-border)]">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="w-full justify-start post-auth-nav-item">
                <User className="w-4 h-4 mr-2" />
                <span className="truncate">{user?.username || 'User'}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem onClick={toggleTheme}>
                {theme === 'dark' ? <Sun className="w-4 h-4 mr-2" /> : <Moon className="w-4 h-4 mr-2" />}
                <span>{theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
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
