'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: 'dashboard' },
  { href: '/analyze', label: 'Analysis', icon: 'psychology' },
  { href: '/chat', label: 'Chat', icon: 'forum' },
  { href: '/resources', label: 'Resources', icon: 'menu_book' },
  { href: '/analytics', label: 'Analytics', icon: 'analytics' },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <>
      {/* Top App Bar */}
      <header className="bg-surface border-b border-outline-variant w-full top-0 sticky z-50 shadow-sm flex justify-between items-center px-4 md:px-8 max-w-[1440px] mx-auto h-16">
        <Link href="/" className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary">monitoring</span>
          <span className="text-primary tracking-tight cursor-pointer font-display text-2xl font-bold">MINDWATCH</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map(item => {
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}
                className={`flex items-center gap-1 px-4 py-2 rounded-full font-label-md transition-colors ${
                  active
                    ? 'text-primary font-bold bg-surface-container-highest'
                    : 'text-on-surface-variant hover:bg-surface-container-highest'
                }`}>
                <span className="material-symbols-outlined text-[20px]"
                  style={active ? { fontVariationSettings: "'FILL' 1" } : {}}>
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-surface-container-highest border border-primary flex items-center justify-center cursor-pointer hover:bg-surface-container transition-colors">
            <span className="material-symbols-outlined text-on-surface text-[20px]">person</span>
          </div>
        </div>
      </header>

      {/* Bottom Nav (mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full flex justify-around items-center py-2 px-4 bg-surface-container border-t border-outline-variant rounded-t-xl shadow-[0px_-4px_20px_0px_rgba(0,0,0,0.4)] z-50">
        {NAV_ITEMS.map(item => {
          const active = pathname === item.href;
          return (
            <Link key={item.href} href={item.href}
              className={`flex flex-col items-center justify-center font-label-md text-xs transition-all active:scale-95 ${
                active
                  ? 'bg-primary-container text-on-primary-container rounded-full px-4 py-1'
                  : 'text-on-surface-variant hover:text-primary'
              }`}>
              <span className="material-symbols-outlined text-[22px]"
                style={active ? { fontVariationSettings: "'FILL' 1" } : {}}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
