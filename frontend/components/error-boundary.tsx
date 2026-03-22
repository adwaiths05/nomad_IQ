'use client'

import React from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface Props {
  children: React.ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary] Error caught:', error, info)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <AlertTriangle className="w-12 h-12 text-red-600 mx-auto mb-4" />
              <h1 className="text-xl font-bold text-slate-900 mb-2">Something went wrong</h1>
              <p className="text-slate-600 mb-2">{this.state.error?.message || 'An unexpected error occurred'}</p>
              <p className="text-sm text-slate-500 mb-6">
                Please try refreshing the page or contact support if the issue persists.
              </p>
              <div className="space-y-3">
                <Button
                  onClick={this.handleReset}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                >
                  Try Again
                </Button>
                <Button
                  onClick={() => window.location.href = '/'}
                  variant="outline"
                  className="w-full"
                >
                  Go to Home
                </Button>
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
