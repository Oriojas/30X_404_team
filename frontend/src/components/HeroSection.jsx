import React from 'react'
import { formatUsd, treasuryHeadroom } from '../api'

export default function HeroSection({ treasury, rules }) {
  const headroom = treasuryHeadroom(treasury.balance_usd, rules.min_treasury_buffer_usd)

  return (
    <section className="w-full py-12 lg:py-16 border-b border-brand-border/60 bg-transparent" id="producto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Left Column (7 cols) */}
          <div className="lg:col-span-7 flex flex-col space-y-6">
            {/* Enterprise Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-brand-border w-fit shadow-xs">
              <span className="text-brand-teal text-xs font-bold">⚡</span>
              <span className="font-mono text-xs text-brand-steel font-semibold tracking-wide">
                B2B Autonomous Financial Ops • Telegram, Gemini & Reglas Deterministas
              </span>
            </div>

            {/* Main Headline */}
            <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-5xl text-brand-navy tracking-tight leading-[1.15]">
              Agentes IA que deciden los pagos de tu empresa{' '}
              <span className="text-brand-teal">sin perder el control</span>
            </h1>

            {/* Subheadline */}
            <p className="text-sm sm:text-base text-brand-muted leading-relaxed font-normal max-w-2xl">
              Automatiza la recepción y evaluación de facturas con visión multimodal (Gemini Flash), validación SARLAFT/OFAC, verificación de saldos en tesorería y conversión a USD con <strong className="text-brand-navy">$0.00 FX Markup</strong>. Aprueba, frena o escala a aprobación humana ante anomalías o reglas críticas.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-1">
              <a
                href="#telegram-demo"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-brand-teal text-white font-semibold text-sm hover:bg-brand-tealHover transition-all shadow-sm active:scale-95"
              >
                <span>Ver Demo en Vivo</span>
                <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
              </a>

              <a
                href="https://t.me/blinka_paybot"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white border border-brand-border text-brand-navy font-semibold text-sm hover:bg-slate-50 transition-all shadow-sm active:scale-95"
              >
                <svg className="w-4 h-4 fill-current text-brand-teal" viewBox="0 0 24 24">
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.121l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.458c.538-.196 1.006.128.832.965z" />
                </svg>
                <span>Probar en Telegram</span>
              </a>
            </div>

            {/* KPI Metrics Strip */}
            <div className="pt-2">
              <div className="grid grid-cols-3 gap-2 sm:gap-4 p-4 rounded-xl bg-white border border-brand-border shadow-sm">
                <div className="flex flex-col">
                  <div className="flex items-center gap-1">
                    <span className="font-display font-bold text-xl sm:text-2xl text-brand-navy">4</span>
                    <span className="material-symbols-outlined text-brand-teal text-[18px]">verified</span>
                  </div>
                  <span className="text-[11px] sm:text-xs text-brand-muted font-medium mt-0.5">Capas de Validación Determinista</span>
                </div>

                <div className="flex flex-col border-l border-brand-border pl-3 sm:pl-4">
                  <div className="flex items-center gap-1">
                    <span className="font-display font-bold text-xl sm:text-2xl text-brand-navy">$0.00</span>
                    <span className="text-xs font-mono font-semibold text-brand-teal">FX</span>
                  </div>
                  <span className="text-[11px] sm:text-xs text-brand-muted font-medium mt-0.5">Markup Cambiario (Blinka)</span>
                </div>

                <div className="flex flex-col border-l border-brand-border pl-3 sm:pl-4">
                  <div className="flex items-center gap-1">
                    <span className="font-display font-bold text-xl sm:text-2xl text-brand-navy">{formatUsd(rules.max_autonomous_usd)}</span>
                    <span className="material-symbols-outlined text-brand-teal text-[18px]">bolt</span>
                  </div>
                  <span className="text-[11px] sm:text-xs text-brand-muted font-medium mt-0.5">Umbral Autónomo (configurable)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (5 cols): Live Treasury & Agent Terminal */}
          <div className="lg:col-span-5 w-full">
            <div className="bg-white rounded-2xl border border-brand-border shadow-xl p-5 sm:p-6 flex flex-col gap-4 relative overflow-hidden">
              {/* Subtle Ambient Radial Highlight */}
              <div className="absolute -top-16 -right-16 w-44 h-44 bg-brand-teal/10 rounded-full blur-3xl pointer-events-none" />

              {/* Header Status Bar */}
              <div className="flex items-center justify-between pb-2 border-b border-brand-border/60">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-teal opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-brand-teal"></span>
                  </span>
                  <span className="font-mono text-xs font-bold text-brand-navy">
                    Blinka Agent Node #01
                  </span>
                </div>

                <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 border border-brand-border">
                  <span className="material-symbols-outlined text-brand-teal text-[14px]">link</span>
                  <span className="font-mono text-[11px] text-brand-steel font-medium">Telegram · FastAPI</span>
                </div>
              </div>

              {/* Active Liquidity Visualizer */}
              <div className="bg-slate-50 p-3.5 rounded-xl border border-brand-border/80 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-brand-muted font-medium">Tesorería Operativa Disponible</span>
                  <span className="font-mono text-sm font-bold text-brand-navy">{formatUsd(treasury.balance_usd, 2)} USD</span>
                </div>

                {/* Liquidity Progress Bar */}
                <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden flex">
                  <div className="bg-brand-teal h-full transition-all duration-500" style={{ width: `${headroom.pct}%` }}></div>
                  <div className="bg-slate-300 h-full flex-1"></div>
                </div>

                <div className="flex items-center justify-between font-mono text-[10px] text-brand-muted">
                  <span>Colchón protegido: {formatUsd(rules.min_treasury_buffer_usd)} USD</span>
                  <span className={`font-semibold ${headroom.ok ? 'text-emerald-700' : 'text-red-600'}`}>
                    Liquidez {headroom.pct}% {headroom.ok ? 'OK' : 'bajo el colchón'}
                  </span>
                </div>
              </div>

              {/* Active Dispatch In-Progress Card */}
              <div className="bg-white p-3.5 rounded-xl border border-brand-border shadow-sm flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-brand-teal font-bold uppercase tracking-wider flex items-center gap-1">
                    <span className="material-symbols-outlined text-[15px] animate-spin">motion_photos_on</span>
                    En Evaluación
                  </span>
                  <span className="font-mono text-xs font-bold text-brand-navy">#BLK-9842</span>
                </div>

                <div className="flex items-center justify-between text-xs pt-1">
                  <div className="flex flex-col">
                    <span className="font-display font-semibold text-sm text-brand-navy">Amazon Web Services</span>
                    <span className="text-[11px] text-brand-muted">Cómputo en la nube us-east-1</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-bold text-sm text-brand-navy block">$1,420.00 USD</span>
                    <span className="text-[10px] font-mono text-brand-teal font-semibold">Aprobado</span>
                  </div>
                </div>
              </div>

              {/* Live Rule Telemetry Stack */}
              <div className="space-y-1.5 font-mono text-xs">
                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-brand-border/60">
                  <span className="text-brand-muted flex items-center gap-1.5 text-[11px]">
                    <span className="material-symbols-outlined text-brand-teal text-[15px]">verified_user</span>
                    Chequeo SARLAFT / OFAC
                  </span>
                  <span className="text-emerald-700 font-semibold text-[11px]">0 MATCHES (CLEAN)</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-brand-border/60">
                  <span className="text-brand-muted flex items-center gap-1.5 text-[11px]">
                    <span className="material-symbols-outlined text-brand-teal text-[15px]">fingerprint</span>
                    Duplicados (30 días)
                  </span>
                  <span className="text-brand-teal font-semibold text-[11px]">ÚNICO</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-brand-border/60">
                  <span className="text-brand-muted flex items-center gap-1.5 text-[11px]">
                    <span className="material-symbols-outlined text-brand-teal text-[15px]">lock_clock</span>
                    Aprobación Autónoma
                  </span>
                  <span className="text-brand-navy font-bold text-[11px]">&lt; $2,000 UMBRAL OK</span>
                </div>
              </div>

              {/* Bottom Micro Status */}
              <div className="flex items-center justify-between pt-1 border-t border-brand-border/60 text-[11px] text-brand-muted">
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px] text-brand-teal">security</span>
                  Audit Log persistido
                </span>
                <span className="font-mono text-brand-steel font-medium">Decisión explicable</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
