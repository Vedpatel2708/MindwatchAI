import type { Metadata } from 'next';
import './globals.css';
import { WebSocketProvider } from '@/components/WebSocketProvider';
import Header from '@/components/Header';

export const metadata: Metadata = {
  title: 'MINDWATCH - Clinical Intelligence',
  description: 'Multi-modal AI platform for early mental health crisis detection',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" />
      </head>
      <body className="bg-background text-on-background min-h-screen pt-16 pb-20 md:pb-0">
        <WebSocketProvider>
          <Header />
          {children}
        </WebSocketProvider>
      </body>
    </html>
  );
}
