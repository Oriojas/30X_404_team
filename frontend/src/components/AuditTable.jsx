import React, { useState } from 'react'
import DashboardMetrics from './DashboardMetrics'
import StatusBadge from './StatusBadge'
import Notice from './Notice'
import { STATUS, STATUS_ORDER, countByStatus, invoiceRef, isRejectedStatus } from '../status'

// Hora relativa a partir de processed_at (ISO del backend)
function timeAgo(iso) {
  const date = iso ? new Date(iso) : null
  if (!date || Number.isNaN(date.getTime())) return 'Reciente'
  const minutes = Math.round((Date.now() - date.getTime()) / 60000)
  if (minutes < 1) return 'Hace un momento'
  if (minutes < 60) return `Hace ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `Hace ${hours} ${hours === 1 ? 'hora' : 'horas'}`
  return date.toLocaleDateString()
}

export default function AuditTable({ invoices = [], loading = false, demoMode = false, refreshError = null, onRefresh, onSelectInvoice, children }) {
  const [activeFilter, setActiveFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  const counts = { ALL: invoices.length, ...countByStatus(invoices) }
  const filters = [['ALL', 'Todos'], ...STATUS_ORDER.map((key) => [key, STATUS[key].label])]

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
            {/* Refresh */}
            <button
              onClick={() => onRefresh && onRefresh()}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-brand-border bg-white text-xs font-semibold text-brand-navy hover:bg-slate-50 disabled:opacity-60 disabled:cursor-wait shrink-0"
            >
              <span className={`material-symbols-outlined text-[16px] ${loading ? 'animate-spin' : ''}`}>refresh</span>
              {loading ? 'Actualizando...' : 'Actualizar'}
            </button>

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
              {filters.map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setActiveFilter(key)}
                  className={`px-3 py-1.5 rounded-lg transition-all whitespace-nowrap ${
                    activeFilter === key
                      ? 'bg-white text-brand-navy font-semibold shadow-xs'
                      : 'text-brand-muted hover:text-brand-navy'
                  }`}
                >
                  {label} ({counts[key]})
                </button>
              ))}
            </div>
          </div>
        </div>

        <DashboardMetrics counts={counts} total={invoices.length} />

        {/* Acciones sobre el Audit Log (subida de facturas) */}
        {children}

        {/* Demo mode banner */}
        {demoMode && (
          <Notice size="lg" icon="cloud_off">
            <span className="font-semibold">Modo demostración:</span> la API no responde, así que se muestran datos
            ficticios. Subir facturas, decidir y guardar reglas está deshabilitado hasta que vuelva la conexión.
          </Notice>
        )}
        {refreshError && (
          <Notice tone="error" size="lg" icon="sync_problem">
            No se pudo actualizar el Audit Log: {refreshError} Se muestran los últimos datos cargados.
          </Notice>
        )}

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
                      {loading && invoices.length === 0
                        ? 'Cargando facturas...'
                        : invoices.length === 0
                        ? 'Aún no hay facturas en el Audit Log. Envía una por Telegram o súbela desde el dashboard.'
                        : 'No se encontraron facturas que coincidan con los filtros seleccionados.'}
                    </td>
                  </tr>
                ) : (
                  filteredInvoices.map((inv, idx) => {
                    const isScaled = inv.decision_status === 'SCALED_TO_HUMAN'
                    const isRejected = isRejectedStatus(inv.decision_status)

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
                            {invoiceRef(inv)}
                          </span>
                          <span className="block text-[11px] text-brand-muted font-sans mt-0.5">
                            {timeAgo(inv.processed_at)}
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
                          <StatusBadge status={inv.decision_status} />
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
