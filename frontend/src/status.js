// Mapa único de estados de decisión: lo comparten la tabla, el Drawer y las métricas.

export const STATUS = {
  AUTO_APPROVED: {
    label: 'Auto-Aprobados',
    badge: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    dot: 'bg-[#10B981]'
  },
  SCALED_TO_HUMAN: {
    label: 'Escalados',
    badge: 'bg-amber-50 text-amber-800 border-amber-200',
    dot: 'bg-[#F59E0B]'
  },
  REJECTED: {
    label: 'Rechazados',
    badge: 'bg-red-50 text-red-800 border-red-200',
    dot: 'bg-[#EF4444]'
  },
  HUMAN_APPROVED: {
    label: 'Aprobados (humano)',
    badge: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    dot: 'bg-[#10B981]',
    human: true
  },
  HUMAN_REJECTED: {
    label: 'Rechazados (humano)',
    badge: 'bg-red-50 text-red-800 border-red-300',
    dot: 'bg-[#EF4444]',
    human: true
  }
}

export const STATUS_ORDER = Object.keys(STATUS)

const FALLBACK = { label: 'Desconocido', badge: 'bg-slate-50 text-slate-700 border-slate-200', dot: 'bg-slate-400' }

export function statusInfo(status) {
  return STATUS[status] || FALLBACK
}

export function isRejectedStatus(status) {
  return status === 'REJECTED' || status === 'HUMAN_REJECTED'
}

export function countByStatus(invoices) {
  const counts = Object.fromEntries(STATUS_ORDER.map((key) => [key, 0]))
  invoices.forEach((inv) => {
    if (inv.decision_status in counts) counts[inv.decision_status] += 1
  })
  return counts
}

// Misión: autonomía = (AUTO_APPROVED + REJECTED) / total. Las decisiones HUMAN_* no cuentan.
export function autonomyRate(counts, total) {
  if (total === 0) return null
  return (counts.AUTO_APPROVED + counts.REJECTED) / total
}

// Referencia visible de una factura (tabla, Drawer y subida)
export function invoiceRef(invoice) {
  return `#${invoice.invoice_number || invoice.id}`
}
