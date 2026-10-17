// Cliente REST del dashboard: único punto que habla con la API de FastAPI.
// Los componentes nunca usan fetch directo.

export const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// Sin autenticación en el MVP: todas las decisiones humanas se registran con este aprobador.
export const DECIDED_BY = 'CFO Demo'

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

export async function saveRules(rules) {
  const { data } = await request('/api/rules', jsonBody('POST', rules))
  return data
}
