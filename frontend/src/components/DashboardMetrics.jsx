import React from 'react'
import { autonomyRate } from '../status'

export default function DashboardMetrics({ counts, total }) {
  const autonomy = autonomyRate(counts, total)
  const autonomyPct = autonomy === null ? null : Math.round(autonomy * 100)
  const humanDecisions = (counts.HUMAN_APPROVED || 0) + (counts.HUMAN_REJECTED || 0)
  const hitlPending = counts.SCALED_TO_HUMAN || 0
  const autoApproved = counts.AUTO_APPROVED || 0
  const rejected = counts.REJECTED || 0

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* KPI 1: Total Facturas */}
      <div className="bg-white rounded-xl border border-brand-border p-4 shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-brand-muted uppercase tracking-wider font-display">
            Total Facturas
          </span>
          <div className="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center text-brand-navy">
            <span className="material-symbols-outlined text-[18px] text-brand-steel">receipt_long</span>
          </div>
        </div>
        <div className="mt-3">
          <div className="flex items-baseline gap-2">
            <span className="font-mono font-bold text-2xl sm:text-3xl text-brand-navy">{total}</span>
            <span className="text-[11px] font-semibold text-emerald-600 flex items-center gap-0.5">
              <span className="material-symbols-outlined text-[14px]">trending_up</span> +100% hoy
            </span>
          </div>
          <p className="mt-1.5 text-xs text-brand-muted font-medium">Telegram, web y API</p>
        </div>
      </div>

      {/* KPI 2: Autonomía */}
      <div className="bg-white rounded-xl border border-brand-border p-4 shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-brand-muted uppercase tracking-wider font-display">
            Autonomía
          </span>
          <div className="w-7 h-7 rounded-lg bg-teal-50 flex items-center justify-center text-brand-teal">
            <span className="material-symbols-outlined text-[18px]">smart_toy</span>
          </div>
        </div>
        <div className="mt-3">
          <div className="flex items-baseline gap-2">
            <span className="font-mono font-bold text-2xl sm:text-3xl text-brand-navy">
              {autonomyPct === null ? '—' : `${autonomyPct}%`}
            </span>
            <span className="text-xs font-mono text-brand-teal font-medium">
              ({autoApproved + rejected} de {total} procesadas)
            </span>
          </div>
          {/* Barra de progreso cian sutil */}
          <div className="mt-2 w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-brand-teal h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${autonomyPct ?? 0}%` }}
            />
          </div>
          <p className="mt-1.5 text-xs text-brand-muted font-medium">
            Auto-aprobadas + rechazadas sin intervención
          </p>
        </div>
      </div>

      {/* KPI 3: Pendientes HITL */}
      <div className="bg-white rounded-xl border border-amber-300/80 p-4 shadow-sm flex flex-col justify-between relative overflow-hidden bg-gradient-to-br from-white to-amber-50/20">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-amber-900 uppercase tracking-wider font-display flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
            Pendientes HITL
          </span>
          <div className="w-7 h-7 rounded-lg bg-amber-100 flex items-center justify-center text-amber-700">
            <span className="material-symbols-outlined text-[18px]">person_alert</span>
          </div>
        </div>
        <div className="mt-3">
          <div className="flex items-baseline gap-2">
            <span className="font-mono font-bold text-2xl sm:text-3xl text-amber-600">{hitlPending}</span>
            {hitlPending > 0 ? (
              <span className="text-[11px] font-semibold text-amber-700 bg-amber-100/70 border border-amber-200 px-2 py-0.5 rounded-full">
                Requiere Atención
              </span>
            ) : (
              <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                Al día
              </span>
            )}
          </div>
          <p className="mt-2 text-xs text-amber-800 font-medium">Esperan decisión en el dashboard</p>
        </div>
      </div>

      {/* KPI 4: Decisiones Humanas */}
      <div className="bg-white rounded-xl border border-brand-border p-4 shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-brand-muted uppercase tracking-wider font-display">
            Decisiones Humanas
          </span>
          <div className="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center text-brand-steel">
            <span className="material-symbols-outlined text-[18px]">how_to_reg</span>
          </div>
        </div>
        <div className="mt-3">
          <div className="flex items-baseline gap-2">
            <span className="font-mono font-bold text-2xl sm:text-3xl text-brand-navy">{humanDecisions}</span>
            <span className="text-xs font-mono text-brand-muted font-medium">Total gestionadas</span>
          </div>
          <p className="mt-2 text-xs text-slate-600 font-medium flex items-center gap-2">
            <span className="text-emerald-700 font-semibold">{counts.HUMAN_APPROVED || 0} aprobadas</span>
            <span className="text-slate-300">·</span>
            <span className="text-rose-600 font-semibold">{counts.HUMAN_REJECTED || 0} rechazadas</span>
          </p>
        </div>
      </div>
    </div>
  )
}
