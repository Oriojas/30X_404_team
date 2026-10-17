import React, { useState, useMemo, useEffect } from 'react'
import DashboardMetrics from './DashboardMetrics'
import StatusBadge from './StatusBadge'
import Notice from './Notice'
import { STATUS, STATUS_ORDER, countByStatus, invoiceRef, isRejectedStatus } from '../status'
import { parseApiDate } from '../api'

const BATCH_SIZE = 5

// Hora relativa y formateada a partir de processed_at (ISO del backend)
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

// Formatea la explicación algorítmica resaltando códigos normativos ([INTEG-03], [HITL-01], etc.)
function formatExplanation(text) {
  if (!text) return null
  const parts = text.split(/(\[[A-Z0-9_-]+\])/g)
  return parts.map((part, i) => {
    if (/^\[[A-Z0-9_-]+\]$/.test(part)) {
      return (
        <span
          key={i}
          className="font-mono text-[10px] font-bold px-1.5 py-0.5 mx-0.5 rounded bg-white/95 border border-slate-300 text-slate-800 shadow-2xs inline-block align-baseline"
        >
          {part}
        </span>
      )
    }
    return part
  })
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
    <section className="w-full py-10 lg:py-14 bg-transparent border-b border-brand-border/60" id="auditoria">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        
        {/* Header de Sección: Auditoría & Explicabilidad • LIVE LOG (Alternativa 1) */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-teal opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-brand-teal"></span>
                </span>
                <h2 className="font-display font-extrabold text-xl sm:text-2xl text-brand-navy tracking-tight">
                  Auditoría &amp; Explicabilidad • <span className="font-mono text-brand-teal tracking-normal">LIVE LOG</span>
                </h2>
              </div>

              {/* Botón Actualizar inline */}
              <button
                onClick={() => onRefresh && onRefresh()}
                disabled={loading}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold text-brand-navy bg-white border border-brand-border hover:bg-slate-50 hover:border-brand-teal transition-all shadow-2xs disabled:opacity-60 disabled:cursor-wait"
                title="Recargar facturas de la API"
              >
                <span className={`material-symbols-outlined text-[15px] text-brand-teal ${loading ? 'animate-spin' : ''}`}>
                  refresh
                </span>
                <span>{loading ? 'Actualizando...' : 'Actualizar'}</span>
              </button>

              {/* Botón de limpiar filtros activos */}
              {activeFiltersCount > 0 && (
                <button
                  onClick={handleClearAllFilters}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-red-200 bg-red-50 text-xs font-semibold text-red-700 hover:bg-red-100 transition-colors shadow-2xs"
                  title="Restablecer todos los filtros del encabezado"
                >
                  <span className="material-symbols-outlined text-[15px]">filter_alt_off</span>
                  <span>Limpiar filtros ({activeFiltersCount})</span>
                </button>
              )}
            </div>
            <p className="text-xs sm:text-sm text-slate-600 font-sans">
              Caja blanca algorítmica: cada decisión del agente incluye trazabilidad explicable y justificación normativa en tiempo real.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-500 bg-white px-3 py-1.5 rounded-lg border border-brand-border shadow-2xs self-start sm:self-auto">
            <span className="material-symbols-outlined text-[16px] text-brand-teal">schedule</span>
            <span>Sincronización: <strong className="text-brand-navy">En tiempo real</strong></span>
          </div>
        </div>

        {/* 4 Tarjetas KPI Institucionales */}
        <DashboardMetrics counts={counts} total={invoices.length} />

        {/* Módulo de Ingesta y Carga de Facturas */}
        {children}

        {/* Banners informativos */}
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

        {/* Tabla de Auditoría con In-Header Filters y Filas Semánticas (Alternativa 1) */}
        <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
          
          {/* Barra superior de la tabla con métrica de eventos y estado del ledger */}
          <div className="px-5 py-3 border-b border-brand-border bg-slate-50/70 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-display font-bold text-brand-navy">Registro de Trazabilidad Criptográfica</span>
              <span className="px-2 py-0.5 rounded-full bg-slate-200/80 text-slate-700 font-mono font-medium text-[11px]">
                {filteredInvoices.length} {filteredInvoices.length === 1 ? 'Evento' : 'Eventos'}
              </span>
            </div>
            <div className="flex items-center gap-3 text-slate-500 font-medium">
              {activeFiltersCount > 0 && (
                <button
                  onClick={handleClearAllFilters}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-red-50 border border-red-200 text-red-700 font-sans text-[11px] font-semibold hover:bg-red-100 transition-colors shadow-2xs"
                  title="Restablecer todos los filtros"
                >
                  <span className="material-symbols-outlined text-[13px]">filter_alt_off</span>
                  <span>Limpiar {activeFiltersCount} filtro{activeFiltersCount > 1 ? 's' : ''}</span>
                </button>
              )}
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[15px] text-slate-400">lock</span>
                SHA-256 Ledger Verificado
              </span>
              <span className="text-slate-300">·</span>
              <span className="text-brand-teal font-mono text-[11px]">4 Capas de Gobernanza</span>
            </div>
          </div>

          {/* Tabla de Alta Densidad */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[960px]">
              
              {/* Encabezado con filtros integrados directamente en cada columna */}
              <thead>
                <tr className="bg-[#F8FAFC] border-b border-brand-border text-slate-700 text-xs font-semibold">
                  
                  {/* Columna 1: ID & HORA */}
                  <th className="py-3 px-3.5 w-[145px] align-top">
                    <div className="space-y-1.5">
                      <span className="block text-[11px] uppercase tracking-wider text-slate-600 font-display whitespace-nowrap">
                        ID &amp; Hora
                      </span>
                      <select
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value)}
                        className="w-full bg-white border border-brand-border text-brand-navy text-xs rounded-md px-2 py-1 outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 transition-all shadow-2xs font-sans"
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
                          className="w-full bg-white border border-brand-border rounded-md px-2 py-0.5 text-[10px] text-brand-navy focus:outline-none focus:border-brand-teal mt-1"
                        />
                      )}
                    </div>
                  </th>

                  {/* Columna 2: PROVEEDOR / CONCEPTO */}
                  <th className="py-3 px-3.5 w-[210px] align-top">
                    <div className="space-y-1.5">
                      <span className="block text-[11px] uppercase tracking-wider text-slate-600 font-display whitespace-nowrap">
                        Proveedor / Concepto
                      </span>
                      <div className="relative">
                        <input
                          type="text"
                          value={vendorFilter}
                          onChange={(e) => setVendorFilter(e.target.value)}
                          placeholder="Filtrar proveedor..."
                          className="w-full bg-white border border-brand-border text-brand-navy text-xs rounded-md pl-6 pr-5 py-1 outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 transition-all shadow-2xs font-sans placeholder:text-slate-400"
                        />
                        <span className="material-symbols-outlined text-[14px] text-slate-400 absolute left-1.5 top-1.5 pointer-events-none">
                          search
                        </span>
                        {vendorFilter && (
                          <button
                            onClick={() => setVendorFilter('')}
                            className="absolute right-1.5 top-1 text-slate-400 hover:text-brand-navy text-xs font-bold"
                            title="Limpiar"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    </div>
                  </th>

                  {/* Columna 3: MONTO USD */}
                  <th className="py-3 px-3.5 w-[150px] align-top text-right">
                    <div className="space-y-1.5">
                      <span className="block text-[11px] uppercase tracking-wider text-slate-600 font-display text-right whitespace-nowrap">
                        Monto USD
                      </span>
                      <select
                        value={amountFilter}
                        onChange={(e) => setAmountFilter(e.target.value)}
                        className="w-full bg-white border border-brand-border text-brand-navy text-xs rounded-md px-2 py-1 outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 transition-all shadow-2xs font-sans text-right"
                        title="Filtrar por monto"
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
                          step="100"
                          value={customAmount}
                          onChange={(e) => setCustomAmount(e.target.value)}
                          placeholder="$ USD"
                          className="w-full bg-white border border-brand-border rounded-md px-2 py-0.5 text-[10px] text-brand-navy focus:outline-none focus:border-brand-teal text-right mt-1"
                        />
                      )}
                    </div>
                  </th>

                  {/* Columna 4: ESTADO */}
                  <th className="py-3 px-3.5 w-[165px] align-top text-center">
                    <div className="space-y-1.5">
                      <span className="block text-[11px] uppercase tracking-wider text-slate-600 font-display text-center whitespace-nowrap">
                        Estado
                      </span>
                      <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="w-full bg-white border border-brand-border text-brand-navy text-xs rounded-md px-2 py-1 outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 transition-all shadow-2xs font-sans text-center"
                        title="Filtrar por estado"
                      >
                        <option value="ALL">Todos ({invoices.length})</option>
                        {STATUS_ORDER.map((key) => (
                          <option key={key} value={key}>
                            {STATUS[key].label} ({counts[key] || 0})
                          </option>
                        ))}
                      </select>
                    </div>
                  </th>

                  {/* Columna 5: JUSTIFICACIÓN CAJA BLANCA */}
                  <th className="py-3 px-3.5 align-top">
                    <div className="space-y-1.5">
                      <span className="block text-[11px] uppercase tracking-wider text-slate-600 font-display whitespace-nowrap">
                        Justificación Caja Blanca
                      </span>
                      <div className="relative">
                        <input
                          type="text"
                          value={explanationFilter}
                          onChange={(e) => setExplanationFilter(e.target.value)}
                          placeholder="Buscar regla o motivo..."
                          className="w-full bg-white border border-brand-border text-brand-navy text-xs rounded-md pl-6 pr-5 py-1 outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 transition-all shadow-2xs font-sans placeholder:text-slate-400"
                        />
                        <span className="material-symbols-outlined text-[14px] text-slate-400 absolute left-1.5 top-1.5 pointer-events-none">
                          search
                        </span>
                        {explanationFilter && (
                          <button
                            onClick={() => setExplanationFilter('')}
                            className="absolute right-1.5 top-1 text-slate-400 hover:text-brand-navy text-xs font-bold"
                            title="Limpiar"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    </div>
                  </th>

                  {/* Columna 6: ACCIÓN */}
                  <th className="py-3 px-3.5 w-[115px] align-top text-right">
                    <div className="space-y-1.5">
                      <span className="block text-[11px] uppercase tracking-wider text-slate-600 font-display text-right whitespace-nowrap">
                        Acción
                      </span>
                      <select
                        value={actionFilter}
                        onChange={(e) => setActionFilter(e.target.value)}
                        className="w-full bg-white border border-brand-border text-brand-navy text-xs rounded-md px-2 py-1 outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal/20 transition-all shadow-2xs font-sans text-right"
                        title="Filtrar por acción"
                      >
                        <option value="ALL">Todas</option>
                        <option value="REVIEW">Revisar</option>
                        <option value="RESOLVED">Detalles</option>
                      </select>
                    </div>
                  </th>

                </tr>
              </thead>

              {/* Cuerpo de la tabla */}
              <tbody className="divide-y divide-brand-border text-xs">
                {displayedInvoices.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="py-12 text-center text-slate-500">
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
                    const isHumanApproved = inv.decision_status === 'HUMAN_APPROVED'

                    return (
                      <tr
                        key={inv.id || idx}
                        className={`transition-colors ${
                          isScaled
                            ? 'bg-amber-50/20 hover:bg-amber-50/50'
                            : isRejected
                            ? 'bg-red-50/15 hover:bg-red-50/40'
                            : 'hover:bg-slate-50/80'
                        } ${idx % 2 === 1 && !isScaled && !isRejected ? 'bg-slate-50/30' : ''}`}
                      >
                        {/* ID & Hora */}
                        <td className="py-3.5 px-4 font-mono align-top">
                          <div className={`font-bold ${isRejected ? 'text-red-600' : isScaled ? 'text-amber-700' : 'text-brand-navy'}`}>
                            {invoiceRef(inv)}
                          </div>
                          <div className="text-[11px] text-slate-400 font-sans mt-0.5">
                            {timeAgo(inv.processed_at)}
                          </div>
                        </td>

                        {/* Proveedor / Concepto */}
                        <td className="py-3.5 px-4 align-top">
                          <div className="font-semibold text-brand-navy">{inv.vendor_name || 'PROVEEDOR_DESCONOCIDO'}</div>
                          <div className="text-[11px] text-slate-500 mt-0.5 truncate max-w-xs font-sans">
                            {inv.concept || 'Servicios Corporativos & Infraestructura'}
                          </div>
                        </td>

                        {/* Monto USD */}
                        <td className="py-3.5 px-4 text-right font-mono align-top">
                          <div className="font-bold text-brand-navy text-sm">
                            ${Number(inv.usd_amount ?? 0).toFixed(2)}{' '}
                            <span className="text-[10px] text-slate-400 font-normal">USD</span>
                          </div>
                          {inv.original_currency && inv.original_currency !== 'USD' && (
                            <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                              ({inv.original_amount?.toLocaleString()} {inv.original_currency})
                            </div>
                          )}
                        </td>

                        {/* Estado Badge */}
                        <td className="py-3.5 px-4 text-center align-top">
                          <StatusBadge status={inv.decision_status} />
                        </td>

                        {/* Justificación Caja Blanca (Callout Box estilizado Alternativa 1) */}
                        <td className="py-3.5 px-4 align-top">
                          <div
                            className={`p-2.5 rounded-lg text-xs leading-relaxed transition-all ${
                              isScaled
                                ? 'bg-amber-50/80 border border-amber-200/90 text-amber-950'
                                : isRejected
                                ? 'bg-red-50/70 border border-red-200/90 text-red-950'
                                : isHumanApproved
                                ? 'bg-teal-50/60 border border-teal-200/80 text-teal-950'
                                : 'bg-emerald-50/50 border border-emerald-200/70 text-slate-800'
                            }`}
                          >
                            <div className="flex items-start gap-1.5">
                              <span
                                className={`material-symbols-outlined text-[16px] shrink-0 mt-0.5 ${
                                  isScaled
                                    ? 'text-amber-600'
                                    : isRejected
                                    ? 'text-red-600'
                                    : isHumanApproved
                                    ? 'text-brand-teal'
                                    : 'text-emerald-600'
                                }`}
                              >
                                {isScaled
                                  ? 'warning'
                                  : isRejected
                                  ? 'gpp_bad'
                                  : isHumanApproved
                                  ? 'how_to_reg'
                                  : 'shield'}
                              </span>
                              <div className="leading-relaxed">
                                {formatExplanation(inv.audit_explanation)}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Acción */}
                        <td className="py-3.5 px-4 text-right align-top">
                          <button
                            onClick={() => onSelectInvoice && onSelectInvoice(inv)}
                            className={`inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shadow-2xs whitespace-nowrap min-w-[76px] ${
                              isScaled
                                ? 'bg-brand-navy hover:bg-brand-steel text-white'
                                : isRejected
                                ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
                                : 'bg-white hover:bg-slate-50 text-slate-700 border border-brand-border'
                            }`}
                          >
                            {isScaled && (
                              <span className="material-symbols-outlined text-[14px] text-brand-teal">
                                edit_note
                              </span>
                            )}
                            <span>{isScaled ? 'Revisar' : 'Detalles'}</span>
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pie de tabla: Carga por lotes e indicador de conteo (Alternativa 1) */}
          <div className="px-5 py-3.5 bg-[#F8FAFC] border-t border-brand-border flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 text-slate-600 font-medium">
              <span className="material-symbols-outlined text-[16px] text-brand-teal">layers</span>
              <span>
                Mostrando <strong className="text-brand-navy font-mono">{displayedInvoices.length}</strong> de{' '}
                <strong className="text-brand-navy font-mono">{filteredInvoices.length}</strong> facturas registradas
                {filteredInvoices.length !== invoices.length && (
                  <span className="text-slate-400 font-sans"> (filtradas de {invoices.length} totales)</span>
                )}
              </span>
              {activeFiltersCount > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-brand-teal/10 text-brand-teal font-medium text-[10px] ml-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-teal"></span>
                  {activeFiltersCount} activo{activeFiltersCount > 1 ? 's' : ''}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {visibleCount < filteredInvoices.length && (
                <>
                  <button
                    onClick={handleLoadMore}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-brand-navy hover:bg-brand-steel transition-colors shadow-2xs"
                  >
                    <span className="material-symbols-outlined text-[16px] text-brand-teal">add_circle</span>
                    <span>Cargar siguientes 5 (+5)</span>
                  </button>
                  <button
                    onClick={handleShowAll}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 bg-white border border-brand-border hover:bg-slate-50 transition-colors"
                  >
                    <span>Mostrar todas ({filteredInvoices.length})</span>
                  </button>
                </>
              )}
              {visibleCount >= filteredInvoices.length && filteredInvoices.length > BATCH_SIZE && (
                <button
                  onClick={handleResetBatch}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-brand-border bg-white hover:bg-slate-50 text-slate-600 hover:text-brand-navy font-medium text-xs transition-colors"
                >
                  <span className="material-symbols-outlined text-[14px]">unfold_less</span>
                  <span>Ver solo las 5 más recientes</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
