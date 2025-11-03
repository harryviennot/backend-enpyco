import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Memoires Techniques API',
  description: 'Backend API for technical memoir generation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  )
}
