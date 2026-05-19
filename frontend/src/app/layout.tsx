import type { Metadata } from 'next'
import { AuthProvider } from '../lib/auth-context'
import { Navbar } from './components/Navbar'
import './globals.css'

export const metadata: Metadata = {
  title: 'NeuroSim - Predictive Creative Intelligence',
  description: 'AI-powered platform that predicts the performance of creator-brand marketing content before launch.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="bg-void">
      <body className="antialiased min-h-screen bg-neural neural-grid font-sans">
        <AuthProvider>
          <Navbar />
          <main className="relative z-10">{children}</main>
        </AuthProvider>
      </body>
    </html>
  )
}
