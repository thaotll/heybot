import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Heybot',
  description: 'HeyBot - KI-gestützte DevOps-Sicherheitsanalyse',
  generator: 'HeyBot',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
