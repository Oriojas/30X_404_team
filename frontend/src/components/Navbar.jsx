import React, { useState } from 'react'

export default function Navbar({ onOpenDemoModal }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="fixed top-0 left-0 w-full z-40 bg-white/95 backdrop-blur-md border-b border-brand-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Logo & SLA Pill */}
        <div className="flex items-center gap-4 sm:gap-6">
          <a href="#" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-brand-navy flex items-center justify-center text-white font-display font-bold text-base shadow-sm group-hover:bg-brand-teal transition-colors">
              B
            </div>
            <span className="font-display font-bold text-lg text-brand-navy tracking-tight">
              Blinka <span className="text-brand-teal font-extrabold">PayBot</span>
            </span>
          </a>

          <div className="hidden sm:inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-brand-border">
            <span className="w-2 h-2 rounded-full bg-brand-teal animate-pulse"></span>
            <span className="font-mono text-xs text-brand-steel font-medium">SLA 99.98% Operativo</span>
          </div>
        </div>

        {/* Center: Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-brand-border">
          <a
            href="#producto"
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-brand-navy bg-white shadow-sm transition-all"
          >
            Producto
          </a>
          <a
            href="#telegram-demo"
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-brand-muted hover:text-brand-navy hover:bg-white/70 transition-all"
          >
            Demo Telegram
          </a>
          <a
            href="#reglas-gobernanza"
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-brand-muted hover:text-brand-navy hover:bg-white/70 transition-all"
          >
            Reglas & Gobernanza
          </a>
          <a
            href="#auditoria"
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-brand-muted hover:text-brand-navy hover:bg-white/70 transition-all"
          >
            Auditoría
          </a>
          <a
            href="#seguridad"
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-brand-muted hover:text-brand-navy hover:bg-white/70 transition-all"
          >
            Seguridad
          </a>
        </nav>

        {/* Right: Action CTAs */}
        <div className="flex items-center gap-3">
          <a
            href="https://t.me/blinka_paybot"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-brand-steel hover:text-brand-navy hover:bg-slate-100 rounded-lg transition-colors border border-transparent hover:border-brand-border"
          >
            <span>Bot Telegram</span>
            <span className="material-symbols-outlined text-[15px]">open_in_new</span>
          </a>

          <button
            onClick={onOpenDemoModal}
            className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-brand-teal text-white text-xs font-semibold shadow-sm hover:bg-brand-tealHover active:scale-95 transition-all"
          >
            Agendar Demo
          </button>

          {/* Mobile menu trigger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 rounded-lg text-brand-steel hover:bg-slate-100"
            aria-label="Abrir menú"
          >
            <span className="material-symbols-outlined text-[22px]">
              {mobileMenuOpen ? 'close' : 'menu'}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Nav Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-brand-border px-4 py-3 space-y-2">
          <a
            href="#producto"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-sm font-semibold text-brand-navy hover:bg-slate-50"
          >
            Producto
          </a>
          <a
            href="#telegram-demo"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-sm text-brand-muted hover:bg-slate-50"
          >
            Demo Telegram
          </a>
          <a
            href="#reglas-gobernanza"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-sm text-brand-muted hover:bg-slate-50"
          >
            Reglas & Gobernanza
          </a>
          <a
            href="#auditoria"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-sm text-brand-muted hover:bg-slate-50"
          >
            Auditoría
          </a>
          <a
            href="#seguridad"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-sm text-brand-muted hover:bg-slate-50"
          >
            Seguridad
          </a>
          <a
            href="https://t.me/blinka_paybot"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between px-3 py-2 rounded-lg text-sm font-semibold text-brand-teal hover:bg-slate-50"
          >
            <span>Abrir Telegram Bot</span>
            <span className="material-symbols-outlined text-[16px]">open_in_new</span>
          </a>
        </div>
      )}
    </header>
  )
}
