import React, { useState } from 'react'

export default function AuditTable({ invoices = [], onSelectInvoice }) {
  const [activeFilter, setActiveFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  const counts = {
    ALL: invoices.length,
    AUTO_APPROVED: invoices.filter((i) => i.decision_status === 'AUTO_APPROVED').length,
    SCALED_TO_HUMAN: invoices.filter((i) => i.decision_status === 'SCALED_TO_HUMAN').length,
    REJECTED: invoices.filter((i) => i.decision_status === 'REJECTED').length
  }

  const filteredInvoices = invoices.filter((inv) => {
    // Filter by tab
    if (activeFilter !== 'ALL' && inv.decision_status !== activeFilter) {
      return false
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const matchesVendor = inv.vendor_name?.toLowerCase().includes(q)
      const matchesFolio = inv.invoice_number?.toLowerCase().includes(q)
      const matchesExplanation = inv.audit_explanation?.toLowerCase().includes(q)
      return matchesVendor || matchesFolio || matchesExplanation
    }

    return true
  })

  return (
    <section className="w-full py-12 lg:py-16 bg-transparent border-b border-brand-border/60" id="auditoria">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Header & Filter Controls */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-teal animate-pulse"></span>
              <h2 className="font-display font-bold text-2xl text-brand-navy tracking-tight">
                Auditoría & Explicabilidad • LIVE LOG
              </h2>
            </div>
            <p className="text-xs text-brand-muted">
              Caja blanca algorítmica: cada decisión del agente incluye trazabilidad explicable y justificación normativa en tiempo real.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {/* Search Input */}
            <div className="relative w-full sm:w-64">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-brand-muted">
                search
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar por proveedor o folio..."
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-brand-border rounded-xl text-xs text-brand-navy outline-none focus:border-brand-teal"
              />
            </div>

            {/* Filter Tabs */}
            <div className="inline-flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-brand-border text-xs font-medium self-start sm:self-auto overflow-x-auto max-w-full">
              <button
                onClick={() => setActiveFilter('ALL')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeFilter === 'ALL'
                    ? 'bg-white text-brand-navy font-semibold shadow-xs'
                    : 'text-brand-muted hover:text-brand-navy'
                }`}
              >
                Todos ({counts.ALL})
              </button>

              <button
                onClick={() => setActiveFilter('AUTO_APPROVED')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeFilter === 'AUTO_APPROVED'
                    ? 'bg-white text-brand-navy font-semibold shadow-xs'
                    : 'text-brand-muted hover:text-brand-navy'
                }`}
              >
                Auto-Aprobados ({counts.AUTO_APPROVED})
              </button>

              <button
                onClick={() => setActiveFilter('SCALED_TO_HUMAN')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeFilter === 'SCALED_TO_HUMAN'
                    ? 'bg-white text-brand-navy font-semibold shadow-xs'
                    : 'text-brand-muted hover:text-brand-navy'
                }`}
              >
                Escalados ({counts.SCALED_TO_HUMAN})
              </button>

              <button
                onClick={() => setActiveFilter('REJECTED')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeFilter === 'REJECTED'
                    ? 'bg-white text-brand-navy font-semibold shadow-xs'
                    : 'text-brand-muted hover:text-brand-navy'
                }`}
              >
                Rechazados ({counts.REJECTED})
              </button>
            </div>
          </div>
        </div>

        {/* Table Container Card */}
        <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-brand-border text-brand-muted font-semibold">
                  <th className="py-3 px-6 text-left">ID & Hora</th>
                  <th className="py-3 px-6 text-left">Proveedor / Concepto</th>
                  <th className="py-3 px-6 text-right">Monto Original / USD</th>
                  <th className="py-3 px-6 text-center">Estado</th>
                  <th className="py-3 px-6 text-left w-2/5">Justificación de Explicabilidad (Caja Blanca)</th>
                  <th className="py-3 px-6 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border">
                {filteredInvoices.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="py-12 text-center text-brand-muted">
                      No se encontraron facturas que coincidan con los filtros seleccionados.
                    </td>
                  </tr>
                ) : (
                  filteredInvoices.map((inv, idx) => {
                    const isAuto = inv.decision_status === 'AUTO_APPROVED'
                    const isScaled = inv.decision_status === 'SCALED_TO_HUMAN'
                    const isRejected = inv.decision_status === 'REJECTED'

                    return (
                      <tr
                        key={inv.id || idx}
                        className={`hover:bg-slate-50/80 transition-colors ${
                          idx % 2 === 1 ? 'bg-slate-50/30' : ''
                        }`}
                      >
                        {/* ID & Hora */}
                        <td className="py-4 px-6 align-top font-mono">
                          <span className={`font-bold ${isRejected ? 'text-red-600' : 'text-brand-navy'}`}>
                            #{inv.invoice_number || `BLK-${inv.id}`}
                          </span>
                          <span className="block text-[11px] text-brand-muted font-sans mt-0.5">
                            {inv.time || 'Reciente'}
                          </span>
                        </td>

                        {/* Proveedor / Concepto */}
                        <td className="py-4 px-6 align-top">
                          <span className="font-semibold text-brand-navy block">{inv.vendor_name}</span>
                          <span className="text-brand-muted text-[11px] block truncate max-w-xs">
                            {inv.concept || 'Servicios Corporativos & Infraestructura'}
                          </span>
                        </td>

                        {/* Monto */}
                        <td className="py-4 px-6 align-top text-right font-mono">
                          <span className="font-bold text-brand-navy block">
                            ${inv.usd_amount ? inv.usd_amount.toFixed(2) : '0.00'} USD
                          </span>
                          {inv.original_currency !== 'USD' && (
                            <span className="text-[11px] text-brand-muted block">
                              ({inv.original_amount?.toLocaleString()} {inv.original_currency})
                            </span>
                          )}
                        </td>

                        {/* Estado */}
                        <td className="py-4 px-6 align-top text-center">
                          {isAuto && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono text-[11px] font-semibold">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]"></span>
                              AUTO_APPROVED
                            </span>
                          )}
                          {isScaled && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-mono text-[11px] font-semibold">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]"></span>
                              SCALED_TO_HUMAN
                            </span>
                          )}
                          {isRejected && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-red-50 text-red-800 border border-red-200 font-mono text-[11px] font-semibold">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444]"></span>
                              REJECTED
                            </span>
                          )}
                        </td>

                        {/* Justificación de Explicabilidad */}
                        <td className="py-4 px-6 align-top text-brand-steel leading-relaxed">
                          {inv.audit_explanation}
                        </td>

                        {/* Acción */}
                        <td className="py-4 px-6 align-top text-right">
                          <button
                            onClick={() => onSelectInvoice && onSelectInvoice(inv)}
                            className={`px-3 py-1 rounded-lg font-semibold text-[11px] transition-colors shadow-xs ${
                              isScaled
                                ? 'bg-brand-navy hover:bg-brand-steel text-white'
                                : isRejected
                                ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
                                : 'bg-slate-100 hover:bg-slate-200 text-brand-navy border border-brand-border'
                            }`}
                          >
                            {isScaled ? 'Revisar' : 'Detalles'}
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  )
}
