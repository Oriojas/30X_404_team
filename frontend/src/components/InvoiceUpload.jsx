import React, { useRef, useState } from 'react'
import StatusBadge from './StatusBadge'
import Notice from './Notice'
import { invoiceRef } from '../status'
import { newIdempotencyKey, uploadInvoice, UPLOAD_ACCEPTED_TYPES, UPLOAD_MAX_BYTES } from '../api'

// 409 = la primera entrega con esta clave aún se procesa: se reintenta con la misma clave
const AUTO_RETRIES_ON_409 = 3
const RETRY_DELAY_MS = 2000

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

function validateFile(file) {
  if (!UPLOAD_ACCEPTED_TYPES.includes(file.type)) {
    return `Tipo de archivo no soportado (${file.type || 'desconocido'}). Usa JPG, PNG, WEBP o PDF.`
  }
  if (file.size > UPLOAD_MAX_BYTES) return 'El archivo supera el límite de 10 MB.'
  if (file.size === 0) return 'El archivo está vacío.'
  return null
}

export default function InvoiceUpload({ readOnly = false, onUploaded, onOpenInvoice }) {
  const inputRef = useRef(null)
  // La Idempotency-Key se genera al elegir el archivo y se reutiliza en cada reintento de ese archivo
  const [selection, setSelection] = useState(null) // { file, key }
  const [phase, setPhase] = useState('idle') // idle | processing | done | error
  const [result, setResult] = useState(null) // { invoice, duplicate }
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    e.target.value = '' // permite volver a elegir el mismo archivo (con una clave nueva)
    if (!file) return
    setResult(null)
    const invalid = validateFile(file)
    if (invalid) {
      setSelection(null)
      setError(invalid)
      setPhase('error')
      return
    }
    setSelection({ file, key: newIdempotencyKey() })
    setError(null)
    setPhase('idle')
  }

  const submit = async () => {
    if (!selection || phase === 'processing') return
    setPhase('processing')
    setError(null)
    for (let attempt = 0; ; attempt += 1) {
      try {
        const uploaded = await uploadInvoice(selection.file, selection.key)
        setResult(uploaded)
        setPhase('done')
        onUploaded && onUploaded(uploaded.invoice)
        return
      } catch (err) {
        if (err.status === 409 && attempt < AUTO_RETRIES_ON_409) {
          await sleep(RETRY_DELAY_MS)
          continue
        }
        setError(err.message || 'No se pudo procesar la factura.')
        setPhase('error')
        return
      }
    }
  }

  const processing = phase === 'processing'
  const invoice = result?.invoice

  return (
    <div className="bg-white rounded-xl border border-brand-border shadow-sm p-4 space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="material-symbols-outlined text-brand-teal text-[20px]">upload_file</span>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-brand-navy">Subir factura</p>
            <p className="text-[11px] text-brand-muted truncate">
              {selection ? selection.file.name : 'JPG, PNG, WEBP o PDF de hasta 10 MB'}
            </p>
          </div>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept={UPLOAD_ACCEPTED_TYPES.join(',')}
          onChange={handleFileChange}
          className="hidden"
        />
        <div className="flex items-center gap-2">
          <button
            onClick={() => inputRef.current?.click()}
            disabled={readOnly || processing}
            className="px-3 py-1.5 rounded-xl border border-brand-border bg-white text-xs font-semibold text-brand-navy hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {selection ? 'Cambiar archivo' : 'Elegir archivo'}
          </button>
          <button
            onClick={submit}
            disabled={readOnly || processing || !selection || phase === 'done'}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-navy hover:bg-brand-steel text-white text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processing && <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>}
            {processing ? 'Procesando...' : phase === 'error' && selection ? 'Reintentar' : 'Procesar factura'}
          </button>
        </div>
      </div>

      {readOnly && (
        <Notice>Modo demostración: la subida se habilita cuando la API responde.</Notice>
      )}

      {processing && (
        <p className="text-[11px] text-brand-muted">Leyendo la factura con Gemini y evaluando las 4 capas. Puede tardar unos segundos.</p>
      )}

      {phase === 'error' && error && (
        <Notice tone="error">{error}</Notice>
      )}

      {phase === 'done' && invoice && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-brand-border text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={invoice.decision_status} />
            <span className="font-mono font-bold text-brand-navy">{invoiceRef(invoice)}</span>
            <span className="text-brand-steel">{invoice.vendor_name || 'Proveedor sin leer'}</span>
            <span className="font-mono text-brand-navy">${(invoice.usd_amount ?? 0).toFixed(2)} USD</span>
            {result.duplicate && <span className="text-[11px] text-brand-muted">(ya se había procesado con esta solicitud)</span>}
          </div>
          <button
            onClick={() => onOpenInvoice && onOpenInvoice(invoice)}
            className="self-start sm:self-auto px-3 py-1 rounded-lg bg-white border border-brand-border text-[11px] font-semibold text-brand-navy hover:bg-slate-100"
          >
            Ver detalle
          </button>
        </div>
      )}
    </div>
  )
}
