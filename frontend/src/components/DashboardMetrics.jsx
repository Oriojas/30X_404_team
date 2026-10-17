import React from 'react'

export default function DashboardMetrics({ metrics = { processed: 0, autoApproved: 0, scaled: 0, rejected: 0, totalUsd: 0 } }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Facturas</span>
        <div className="text-2xl font-bold text-slate-800 mt-1">{metrics.processed}</div>
        <span className="text-xs text-slate-400 mt-1 block">Canal Telegram & API</span>
      </div>

      <div className="bg-white p-5 rounded-xl border border-emerald-100 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600">Auto-Aprobadas</span>
        <div className="text-2xl font-bold text-emerald-700 mt-1">{metrics.autoApproved}</div>
        <span className="text-xs text-emerald-500 mt-1 block">&le; $2,000 USD sin intervención</span>
      </div>

      <div className="bg-white p-5 rounded-xl border border-amber-100 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wider text-amber-600">Escaladas HITL</span>
        <div className="text-2xl font-bold text-amber-700 mt-1">{metrics.scaled}</div>
        <span className="text-xs text-amber-500 mt-1 block">Aprobación en 1 clic Telegram</span>
      </div>

      <div className="bg-white p-5 rounded-xl border border-rose-100 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wider text-rose-600">Rechazadas</span>
        <div className="text-2xl font-bold text-rose-700 mt-1">{metrics.rejected}</div>
        <span className="text-xs text-rose-500 mt-1 block">SARLAFT / Duplicados</span>
      </div>
    </div>
  )
}
