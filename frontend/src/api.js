// Cliente REST del dashboard: único punto que habla con la API de FastAPI.
// Los componentes nunca usan fetch directo.

export const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// Sin autenticación en el MVP: todas las decisiones humanas se registran con este aprobador.
export const DECIDED_BY = 'CFO Demo'

// Reglas por defecto mientras no llegan las de la API (o en modo demostración)
export const DEFAULT_RULES = {
  max_autonomous_usd: 2000,
  sarlaft_check_enabled: true,
  duplicate_check_days: 30,
  min_treasury_buffer_usd: 1000
}

// Tesorería del seed de demostración: solo en modo demostración (con la API viva nunca se finge un saldo)
export const DEFAULT_TREASURY = {
  balance_usd: 8500,
  committed_usd: 0,
  available_usd: 8500,
  snapshot_at: null,
  monthly_budget_usd: 25000,
  month_spent_usd: 0
}

// Disponible = saldo de la foto − pagos aprobados después de ella (FIN-01 y FIN-03 deciden con este valor).
// Un backend anterior a la Fase 6 no envía available_usd: el disponible es el saldo.
export function availableUsd(treasury) {
  if (!treasury || treasury.balance_usd == null) return null
  if (treasury.available_usd != null) return treasury.available_usd
  return treasury.balance_usd - (treasury.committed_usd ?? 0)
}

// Presupuesto del período (FIN-02): gastado y restante del mes; null si falta el presupuesto.
export function budgetUsage(treasury) {
  if (!treasury || treasury.monthly_budget_usd == null) return null
  const budget = Number(treasury.monthly_budget_usd)
  const spent = Number(treasury.month_spent_usd ?? 0)
  if (!Number.isFinite(budget) || !Number.isFinite(spent)) return null
  const pct = budget > 0 ? Math.min(100, (spent / budget) * 100) : 100
  return { budget, spent, remaining: budget - spent, pct, ok: spent < budget }
}

// Holgura sobre el colchón: qué parte del disponible queda libre por encima de la reserva (FIN-03).
// null si falta el saldo o la reserva no es un número válido (p. ej. el campo está vacío mientras se edita).
export function treasuryHeadroom(balanceUsd, bufferUsd) {
  if (balanceUsd == null || bufferUsd == null || bufferUsd === '') return null
  const balance = Number(balanceUsd)
  const buffer = Number(bufferUsd)
  if (!Number.isFinite(balance) || !Number.isFinite(buffer) || buffer < 0) return null
  const ok = balance > buffer
  const pct = ok ? Math.min(100, ((balance - buffer) / balance) * 100) : 0
  const rounded = Math.round(pct)
  // Por encima del colchón pero por menos de medio punto: "<1%" en vez de un "0% OK" contradictorio
  return { pct, ok, label: ok && rounded === 0 ? '<1%' : `${rounded}%` }
}

export function headroomText(headroom) {
  if (!headroom) return '—'
  return `${headroom.label} ${headroom.ok ? 'OK' : 'bajo el colchón'}`
}

export function headroomColor(headroom) {
  if (!headroom) return 'text-brand-muted'
  return headroom.ok ? 'text-emerald-700' : 'text-red-600'
}

// Negativos como "-$1,950" (p. ej. un disponible sobregirado por una excepción aprobada), no "$-1,950"
export function formatUsd(amount, decimals = 0) {
  const value = Number(amount || 0)
  const text = Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  return `${value < 0 ? '-' : ''}$${text}`
}

// El backend guarda las fechas en UTC y las envía con "Z". Una fecha sin zona (backend anterior)
// también es UTC: se le agrega "Z" para que el navegador no la tome como hora local.
export function parseApiDate(iso) {
  if (!iso) return null
  const withZone = /(Z|[+-]\d{2}:?\d{2})$/.test(iso) || !iso.includes('T') ? iso : `${iso}Z`
  return new Date(withZone)
}

// crypto.randomUUID solo existe en contextos seguros (HTTPS o localhost); en HTTP por la red local
// (vite con host: true) se arma un UUID v4 con getRandomValues, que sí está disponible.
export function newIdempotencyKey() {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

export const UPLOAD_ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
export const UPLOAD_MAX_BYTES = 10 * 1024 * 1024

export class ApiError extends Error {
  // status 0 significa que la API no respondió (red caída o sin VITE_API_BASE_URL)
  constructor(status, message, detail = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }

  // Errores de validación de FastAPI (422) agrupados por campo: { campo: 'mensaje' }
  get fieldErrors() {
    if (!Array.isArray(this.detail)) return {}
    return this.detail.reduce((acc, item) => {
      const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : null
      if (field && !acc[field]) acc[field] = item.msg
      return acc
    }, {})
  }
}

function detailToMessage(detail, status) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((item) => item.msg).join('. ')
  }
  return `La API respondió con el código ${status}.`
}

async function request(path, options = {}) {
  if (!API_BASE) {
    throw new ApiError(0, 'La API no está configurada (falta VITE_API_BASE_URL).')
  }

  let res
  try {
    res = await fetch(`${API_BASE}${path}`, options)
  } catch {
    throw new ApiError(0, 'No se pudo conectar con la API.')
  }

  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data?.detail ?? null
    throw new ApiError(res.status, detailToMessage(detail, res.status), detail)
  }
  return { status: res.status, data }
}

function jsonBody(method, body) {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }
}

export async function listInvoices() {
  const { data } = await request('/api/invoices')
  return Array.isArray(data) ? data : []
}

// 201 (nueva) y 200 (misma Idempotency-Key ya procesada) devuelven la factura igual.
// 409 llega como ApiError: la primera entrega con esa clave aún se procesa.
export async function uploadInvoice(file, idempotencyKey) {
  const form = new FormData()
  form.append('file', file)
  const { status, data } = await request('/api/invoices/upload', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: form
  })
  return { invoice: data, duplicate: status === 200 }
}

// decision: 'APPROVE' | 'REJECT'. 409 si la factura ya no está en SCALED_TO_HUMAN.
export async function decideInvoice(invoiceId, decision, note) {
  const { data } = await request(
    `/api/invoices/${invoiceId}/decision`,
    jsonBody('POST', { decision, decided_by: DECIDED_BY, note: note?.trim() || null })
  )
  return data
}

export async function getRules() {
  const { data } = await request('/api/rules')
  return data
}

export async function getTreasury() {
  const { data } = await request('/api/treasury')
  return data
}

export async function saveRules(rules) {
  const { data } = await request('/api/rules', jsonBody('POST', rules))
  return data
}
