import React, { useState, useMemo, useEffect } from 'react'
import DashboardMetrics from './DashboardMetrics'
import StatusBadge from './StatusBadge'
import Notice from './Notice'
import { STATUS, STATUS_ORDER, countByStatus, invoiceRef, isRejectedStatus } from '../status'
import { parseApiDate } from '../api'

const BATCH_SIZE = 5

// Hora relativa a partir de processed_at (ISO del backend)
function timeAgo(iso) {
  const date = parseApiDate(iso)
  if (!date || Number.isNaN(date.getTime())) return 'Reciente'
  const minutes = Math.round((Date.now() - date.getTime()) / 60000)
  if (minutes < 1) return 'Hace un momento'
  if (minutes < 60) return `Hace ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `Hace ${hours} ${hours === 1 ? 'hora' : 'horas'}`
  return date.toLocaleDateString()
}

export default function AuditTable({
  invoices = [],
  loading = false,
  demoMode = false,
  refreshError = null,
  onRefresh,
  onSelectInvoice,
  children
}) {
  // Filtros de columna en encabezado
  const [dateFilter, setDateFilter] = useState('ALL')
  const [customDate, setCustomDate] = useState('')
  const [vendorFilter, setVendorFilter] = useState('')
  const [amountFilter, setAmountFilter] = useState('ALL')
  const [customAmount, setCustomAmount] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [explanationFilter, setExplanationFilter] = useState('')
  const [actionFilter, setActionFilter] = useState('ALL')

  // Carga por lotes (inicia mostrando las 5 más recientes)
  const [visibleCount, setVisibleCount] = useState(BATCH_SIZE)

  // Métricas para DashboardMetrics
  const counts = { ALL: invoices.length, ...countByStatus(invoices) }

  // 1. Ordenar por fecha más reciente primero (processed_at desc)
  const sortedInvoices = useMemo(() => {
    return [...invoices].sort((a, b) => {
      const da = a.processed_at ? parseApiDate(a.processed_at)?.getTime() || 0 : 0
      const db = b.processed_at ? parseApiDate(b.processed_at)?.getTime() || 0 : 0
      return db - da
    })
  }, [invoices])

  // 2. Aplicar los filtros del encabezado
  const filteredInvoices = useMemo(() => {
    return sortedInvoices.filter((inv) => {
      // Filtro de Fecha
      if (dateFilter !== 'ALL') {
        const date = parseApiDate(inv.processed_at)
        if (!date || Number.isNaN(date.getTime())) return false
        const now = Date.now()
        const diffMs = now - date.getTime()
        const diffDays = diffMs / (1000 * 60 * 60 * 24)

        if (dateFilter === 'TODAY') {
          const isToday = date.toDateString() === new Date().toDateString() || diffDays <= 1
          if (!isToday) return false
        } else if (dateFilter === '7D') {
          if (diffDays > 7) return false
        } else if (dateFilter === '30D') {
          if (diffDays > 30) return false
        } else if (dateFilter === 'CUSTOM' && customDate) {
          const invYmd = date.toISOString().slice(0, 10)
          if (invYmd !== customDate) return false
        }
      }

      // Filtro de Proveedor / Concepto / Folio
      if (vendorFilter.trim()) {
        const q = vendorFilter.toLowerCase().trim()
        const matchVendor = inv.vendor_name?.toLowerCase().includes(q)
        const matchConcept = inv.concept?.toLowerCase().includes(q)
        const matchFolio = inv.invoice_number?.toLowerCase().includes(q)
        if (!matchVendor && !matchConcept && !matchFolio) return false
      }

      // Filtro de Monto
      const amount = Number(inv.usd_amount ?? 0)
      if (amountFilter === 'UNDER_2000' && amount > 2000) return false
      if (amountFilter === 'OVER_2000' && amount <= 2000) return false
      if (amountFilter === 'CUSTOM_MIN' && customAmount !== '' && amount < Number(customAmount)) return false
      if (amountFilter === 'CUSTOM_MAX' && customAmount !== '' && amount > Number(customAmount)) return false

      // Filtro de Estado
      if (statusFilter !== 'ALL' && inv.decision_status !== statusFilter) return false

      // Filtro de Explicación / Regla
      if (explanationFilter.trim()) {
        const q = explanationFilter.toLowerCase().trim()
        if (!inv.audit_explanation?.toLowerCase().includes(q)) return false
      }

      // Filtro de Acción
      if (actionFilter === 'REVIEW' && inv.decision_status !== 'SCALED_TO_HUMAN') return false
      if (actionFilter === 'RESOLVED' && inv.decision_status === 'SCALED_TO_HUMAN') return false

      return true
    })
  }, [
    sortedInvoices,
    dateFilter,
    customDate,
    vendorFilter,
    amountFilter,
    customAmount,
    statusFilter,
    explanationFilter,
    actionFilter
  ])

  // Al cambiar cualquier filtro, reiniciar visibleCount a 5 para mostrar las 5 más recientes del conjunto filtrado
  useEffect(() => {
    setVisibleCount(BATCH_SIZE)
  }, [
    dateFilter,
    customDate,
    vendorFilter,
    amountFilter,
    customAmount,
    statusFilter,
    explanationFilter,
    actionFilter
  ])

  // Conteo de filtros activos
  const activeFiltersCount = useMemo(() => {
    return [
      dateFilter !== 'ALL',
      vendorFilter.trim() !== '',
      amountFilter !== 'ALL',
      statusFilter !== 'ALL',
      explanationFilter.trim() !== '',
      actionFilter !== 'ALL'
    ].filter(Boolean).length
  }, [dateFilter, vendorFilter, amountFilter, statusFilter, explanationFilter, actionFilter])

  // Restablecer todos los filtros
  const handleClearAllFilters = () => {
    setDateFilter('ALL')
    setCustomDate('')
    setVendorFilter('')
    setAmountFilter('ALL')
    setCustomAmount('')
    setStatusFilter('ALL')
    setExplanationFilter('')
    setActionFilter('ALL')
    setVisibleCount(BATCH_SIZE)
  }

  // Controles de carga por lotes
  const displayedInvoices = filteredInvoices.slice(0, visibleCount)

  const handleLoadMore = () => {
    setVisibleCount((prev) => Math.min(prev + BATCH_SIZE, filteredInvoices.length))
  }

  const handleShowAll = () => {
    setVisibleCount(filteredInvoices.length)
  }

  const handleResetBatch = () => {
    setVisibleCount(BATCH_SIZE)
  }

  return (
    <section className="w-full py-12 lg:py-16 bg-transparent border-b border-brand-border/60" id="auditoria">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Header & Controls */}
        <div className="space-y-1">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-teal animate-pulse"></span>
              <h2 className="font-display font-bold text-2xl text-brand-navy tracking-tight">
                Auditoría & Explicabilidad • LIVE LOG
              </h2>
            </div>

            {/* Botón Actualizar reubicado inline junto al título */}
            <button
              onClick={() => onRefresh && onRefresh()}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-brand-border bg-white text-xs font-semibold text-brand-navy hover:bg-slate-50 hover:border-brand-teal/40 disabled:opacity-60 disabled:cursor-wait shrink-0 shadow-2xs transition-all"
              title="Recargar facturas de la API"
            >
              <span className={`material-symbols-outlined text-[15px] ${loading ? 'animate-spin' : ''}`}>refresh</span>
              {loading ? 'Actualizando...' : 'Actualizar'}
            </button>

            {/* Botón de limpiar filtros activos si hay alguno aplicado */}
            {activeFiltersCount > 0 && (
              <button
                onClick={handleClearAllFilters}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-red-200 bg-red-50 text-xs font-semibold text-red-700 hover:bg-red-100 transition-colors shadow-2xs"
                title="Restablecer todos los filtros del encabezado"
              >
                <span className="material-symbols-outlined text-[15px]">filter_alt_off</span>
                Limpiar filtros ({activeFiltersCount})
              </button>
            )}
          </div>
          <p className="text-xs text-brand-muted">
            Caja blanca algorítmica: cada decisión del agente incluye trazabilidad explicable y justificación normativa en tiempo real.
          </p>
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
                {/* Fila 1: Títulos de columna */}
                <tr className="bg-slate-50 border-b border-brand-border text-brand-muted font-semibold text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-4 text-left w-44">ID & Hora</th>
                  <th className="py-3 px-4 text-left min-w-[200px]">Proveedor / Concepto</th>
                  <th className="py-3 px-4 text-right w-44">Monto (USD)</th>
                  <th className="py-3 px-4 text-center w-40">Estado</th>
                  <th className="py-3 px-4 text-left min-w-[260px]">Justificación (Caja Blanca)</th>
                  <th className="py-3 px-4 text-right w-36">Acción</th>
                </tr>

                {/* Fila 2: Filtros integrados dentro del encabezado */}
                <tr className="bg-slate-100/90 border-b border-brand-border text-xs">
                  {/* Filtro: Fecha / Hora */}
                  <th className="py-2.5 px-3 align-top font-normal">
                    <div className="space-y-1">
                      <select
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value)}
                        className="w-full bg-white border border-brand-border rounded-lg px-2 py-1 text-[11px] text-brand-navy focus:outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 shadow-2xs"
                        title="Filtrar por fecha"
                      >
                        <option value="ALL">Todas las fechas</option>
                        <option value="TODAY">Hoy</option>
                        <option value="7D">Últimos 7 días</option>
                        <option value="30D">Últimos 30 días</option>
                        <option value="CUSTOM">Fecha específica...</option>
                      </select>
                      {dateFilter === 'CUSTOM' && (
                        <input
                          type="date"
                          value={customDate}
                          onChange={(e) => setCustomDate(e.target.value)}
                          className="w-full bg-white border border-brand-border rounded-lg px-2 py-0.5 text-[10px] text-brand-navy focus:outline-none focus:border-brand-teal"
                        />
                      )}
                    </div>
                  </th>

                  {/* Filtro: Proveedor / Concepto */}
                  <th className="py-2.5 px-3 align-top font-normal">
                    <div className="relative">
                      <input
                        type="text"
                        value={vendorFilter}
                        onChange={(e) => setVendorFilter(e.target.value)}
                        placeholder="Filtrar proveedor..."
                        className="w-full bg-white border border-brand-border rounded-lg pl-2 pr-6 py-1 text-[11px] text-brand-navy placeholder:text-brand-muted/70 focus:outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 shadow-2xs"
                      />
                      {vendorFilter && (
                        <button
                          onClick={() => setVendorFilter('')}
                          className="absolute right-2 top-1 text-brand-muted hover:text-brand-navy text-xs font-bold"
                          title="Limpiar proveedor"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  </th>

                  {/* Filtro: Monto */}
                  <th className="py-2.5 px-3 align-top font-normal">
                    <div className="space-y-1">
                      <select
                        value={amountFilter}
                        onChange={(e) => setAmountFilter(e.target.value)}
                        className="w-full bg-white border border-brand-border rounded-lg px-2 py-1 text-[11px] text-brand-navy focus:outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 shadow-2xs"
                        title="Filtrar por rango de monto"
                      >
                        <option value="ALL">Todos los montos</option>
                        <option value="UNDER_2000">≤ $2,000 USD (Autónomo)</option>
                        <option value="OVER_2000">&gt; $2,000 USD (Escalado)</option>
                        <option value="CUSTOM_MIN">Mínimo USD...</option>
                        <option value="CUSTOM_MAX">Máximo USD...</option>
                      </select>
                      {amountFilter.startsWith('CUSTOM') && (
                        <input
                          type="number"
                          min="0"
                          step="50"
                          value={customAmount}
                          onChange={(e) => setCustomAmount(e.target.value)}
                          placeholder="$ USD"
                          className="w-full bg-white border border-brand-border rounded-lg px-2 py-0.5 text-[10px] text-brand-navy focus:outline-none focus:border-brand-teal"
                        />
                      )}
                    </div>
                  </th>

                  {/* Filtro: Estado */}
                  <th className="py-2.5 px-3 align-top font-normal">
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="w-full bg-white border border-brand-border rounded-lg px-2 py-1 text-[11px] text-brand-navy focus:outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 shadow-2xs"
                      title="Filtrar por estado de decisión"
                    >
                      <option value="ALL">Todos ({invoices.length})</option>
                      {STATUS_ORDER.map((key) => (
                        <option key={key} value={key}>
                          {STATUS[key].label} ({counts[key] || 0})
                        </option>
                      ))}
                    </select>
                  </th>

                  {/* Filtro: Justificación / Caja Blanca */}
                  <th className="py-2.5 px-3 align-top font-normal">
                    <div className="relative">
                      <input
                        type="text"
                        value={explanationFilter}
                        onChange={(e) => setExplanationFilter(e.target.value)}
                        placeholder="Buscar regla o motivo..."
                        className="w-full bg-white border border-brand-border rounded-lg pl-2 pr-6 py-1 text-[11px] text-brand-navy placeholder:text-brand-muted/70 focus:outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 shadow-2xs"
                      />
                      {explanationFilter && (
                        <button
                          onClick={() => setExplanationFilter('')}
                          className="absolute right-2 top-1 text-brand-muted hover:text-brand-navy text-xs font-bold"
                          title="Limpiar búsqueda"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  </th>

                  {/* Filtro: Acción */}
                  <th className="py-2.5 px-3 align-top font-normal text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <select
                        value={actionFilter}
                        onChange={(e) => setActionFilter(e.target.value)}
                        className="w-full bg-white border border-brand-border rounded-lg px-2 py-1 text-[11px] text-brand-navy focus:outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 shadow-2xs"
                        title="Filtrar por tipo de acción"
                      >
                        <option value="ALL">Todas</option>
                        <option value="REVIEW">Requiere Revisión</option>
                        <option value="RESOLVED">Informativas</option>
                      </select>
                      {activeFiltersCount > 0 && (
                        <button
                          onClick={handleClearAllFilters}
                          className="p-1 rounded-lg hover:bg-slate-200 text-brand-muted hover:text-red-600 transition-colors shrink-0"
                          title="Restablecer todos los filtros"
                        >
                          <span className="material-symbols-outlined text-[16px]">filter_alt_off</span>
                        </button>
                      )}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border">
                {displayedInvoices.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="py-12 text-center text-brand-muted">
                      {loading && invoices.length === 0 ? (
                        'Cargando facturas...'
                      ) : invoices.length === 0 ? (
                        'Aún no hay facturas en el Audit Log. Envía una por Telegram o súbela desde el dashboard.'
                      ) : (
                        <div className="space-y-2">
                          <p>No se encontraron facturas que coincidan con los filtros seleccionados.</p>
                          <button
                            onClick={handleClearAllFilters}
                            className="inline-flex items-center gap-1 text-xs text-brand-teal hover:underline font-semibold"
                          >
                            <span className="material-symbols-outlined text-[14px]">refresh</span>
                            Limpiar filtros para ver todas
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ) : (
                  displayedInvoices.map((inv, idx) => {
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
                        <td className="py-4 px-4 align-top font-mono">
                          <span className={`font-bold ${isRejected ? 'text-red-600' : 'text-brand-navy'}`}>
                            {invoiceRef(inv)}
                          </span>
                          <span className="block text-[11px] text-brand-muted font-sans mt-0.5">
                            {timeAgo(inv.processed_at)}
                          </span>
                        </td>

                        {/* Proveedor / Concepto */}
                        <td className="py-4 px-4 align-top">
                          <span className="font-semibold text-brand-navy block">{inv.vendor_name}</span>
                          <span className="text-brand-muted text-[11px] block truncate max-w-xs">
                            {inv.concept || 'Servicios Corporativos & Infraestructura'}
                          </span>
                        </td>

                        {/* Monto */}
                        <td className="py-4 px-4 align-top text-right font-mono">
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
                        <td className="py-4 px-4 align-top text-center">
                          <StatusBadge status={inv.decision_status} />
                        </td>

                        {/* Justificación de Explicabilidad */}
                        <td className="py-4 px-4 align-top text-brand-steel leading-relaxed">
                          {inv.audit_explanation}
                        </td>

                        {/* Acción */}
                        <td className="py-4 px-4 align-top text-right">
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

          {/* Pie de tabla: Carga por lotes e indicador de conteo */}
          <div className="bg-slate-50/90 border-t border-brand-border px-4 sm:px-6 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-brand-muted">
            <div className="flex items-center gap-2 flex-wrap">
              <span>
                Mostrando <strong className="text-brand-navy font-semibold">{displayedInvoices.length}</strong> de{' '}
                <strong className="text-brand-navy font-semibold">{filteredInvoices.length}</strong> facturas
                {filteredInvoices.length !== invoices.length && (
                  <span className="text-brand-muted/80"> (filtradas de {invoices.length} totales)</span>
                )}
              </span>
              {activeFiltersCount > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-brand-teal/10 text-brand-teal font-medium text-[10px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-teal"></span>
                  {activeFiltersCount} filtro{activeFiltersCount > 1 ? 's' : ''} activo{activeFiltersCount > 1 ? 's' : ''}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {visibleCount < filteredInvoices.length && (
                <>
                  <button
                    onClick={handleLoadMore}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-navy hover:bg-brand-steel text-white font-semibold text-xs shadow-xs transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px]">add_circle</span>
                    Cargar siguientes 5 (+5)
                  </button>
                  <button
                    onClick={handleShowAll}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-brand-border bg-white hover:bg-slate-100 text-brand-navy font-medium text-xs transition-colors"
                  >
                    Mostrar todas ({filteredInvoices.length})
                  </button>
                </>
              )}
              {visibleCount >= filteredInvoices.length && filteredInvoices.length > BATCH_SIZE && (
                <button
                  onClick={handleResetBatch}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-brand-border bg-white hover:bg-slate-100 text-brand-muted hover:text-brand-navy font-medium text-xs transition-colors"
                >
                  <span className="material-symbols-outlined text-[14px]">unfold_less</span>
                  Ver solo las 5 más recientes
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
