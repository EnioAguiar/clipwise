import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ClipWise',
  description: 'Detector de momentos para lives',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body className="dark">{children}</body>
    </html>
  )
}