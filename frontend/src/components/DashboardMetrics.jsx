import React from 'react'
import { autonomyRate } from '../status'

// counts: conteo por estado ya calculado en el Audit Log
export default function DashboardMetrics({ counts, total }) {
  const autonomy = autonomyRate(counts, total)
  const humanDecisions = counts.HUMAN_APPROVED + counts.HUMAN_REJECTED

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div className="bg-white p-4 rounded-xl border border-brand-border shadow-sm">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-muted">Total Facturas</span>
        <div className="text-2xl font-bold text-brand-navy mt-1">{total}</div>
        <span className="text-[11px] text-brand-muted mt-1 block">Telegram, web y API</span>
      </div>

      <div className="bg-white p-4 rounded-xl border border-teal-100 shadow-sm">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-teal">Autonomía</span>
        <div className="text-2xl font-bold text-brand-navy mt-1">
          {autonomy === null ? '—' : `${Math.round(autonomy * 100)}%`}
        </div>
        <span className="text-[11px] text-brand-muted mt-1 block">Auto-aprobadas + rechazadas sin intervención</span>
      </div>

      <div className="bg-white p-4 rounded-xl border border-amber-100 shadow-sm">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-600">Pendientes HITL</span>
        <div className="text-2xl font-bold text-amber-700 mt-1">{counts.SCALED_TO_HUMAN}</div>
        <span className="text-[11px] text-amber-600 mt-1 block">Esperan decisión en el dashboard</span>
      </div>

      <div className="bg-white p-4 rounded-xl border border-brand-border shadow-sm">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-muted">Decisiones Humanas</span>
        <div className="text-2xl font-bold text-brand-navy mt-1">{humanDecisions}</div>
        <span className="text-[11px] text-brand-muted mt-1 block">
          {counts.HUMAN_APPROVED} aprobadas · {counts.HUMAN_REJECTED} rechazadas
        </span>
      </div>
    </div>
  )
}
