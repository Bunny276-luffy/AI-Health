import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'NeuroScan - Uncertainty-Aware AI Tumor Detection System',
  description: 'Advanced medical imaging dashboard with uncertainty estimation and longitudinal progression analysis.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} bg-slate-900 text-slate-50 min-h-screen selection:bg-blue-500/30`}>
        {children}
        <Toaster 
          position="bottom-right" 
          toastOptions={{
            style: {
              background: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #1e293b',
            },
          }} 
        />
      </body>
    </html>
  )
}
