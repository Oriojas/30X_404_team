import React from 'react'

export default function Footer() {
  return (
    <footer className="w-full bg-slate-50 border-t border-brand-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 pb-8 border-b border-brand-border/60">
          {/* Logo & Vision */}
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-brand-navy flex items-center justify-center text-white font-display font-bold text-sm">
                B
              </div>
              <span className="font-display font-bold text-base text-brand-navy tracking-tight">
                Blinka <span className="text-brand-teal">PayBot</span>
              </span>
            </div>
            <p className="text-xs text-brand-muted max-w-sm leading-relaxed">
              Infraestructura financiera autónoma de agentes de pago con aprobación gobernada, motor FX a $0 Markup y auditoría explicable en tiempo real.
            </p>
          </div>

          {/* Compliance Badges */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-brand-border shadow-2xs">
              <span className="material-symbols-outlined text-brand-teal text-[16px]">verified_user</span>
              <span className="font-mono text-xs text-brand-navy font-semibold">Reglas Deterministas</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-brand-border shadow-2xs">
              <span className="material-symbols-outlined text-brand-teal text-[16px]">lock</span>
              <span className="font-mono text-xs text-brand-navy font-semibold">Audit Log Explicable</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-brand-border shadow-2xs">
              <span className="material-symbols-outlined text-brand-teal text-[16px]">gavel</span>
              <span className="font-mono text-xs text-brand-navy font-semibold">Reglas SARLAFT</span>
            </div>
          </div>
        </div>

        {/* Bottom Row */}
        <div className="pt-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-brand-muted">
          <div className="flex flex-wrap items-center gap-4 sm:gap-6">
            <a href="#producto" className="hover:text-brand-navy transition-colors">
              Producto
            </a>
            <a href="#telegram-demo" className="hover:text-brand-navy transition-colors">
              Demo Telegram
            </a>
            <a href="#reglas-gobernanza" className="hover:text-brand-navy transition-colors">
              Reglas & Gobernanza
            </a>
            <a href="#auditoria" className="hover:text-brand-navy transition-colors">
              Auditoría
            </a>
            <a href="#seguridad" className="hover:text-brand-navy transition-colors">
              Seguridad & KYC
            </a>
          </div>

          <div className="text-center md:text-right">
            <span>Blinka PayAgent © 2026 — Hackathon 30X | Equipo 404 (Oscar Riojas & Luis Felipe Marín)</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
