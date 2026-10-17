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
    <div className="bg-white rounded-xl border border-brand-border shadow-sm p-4 sm:px-6 sm:py-4 space-y-3">
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        
        {/* Header con icono institucional */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-brand-navy shrink-0">
            <span className="material-symbols-outlined text-[22px] text-brand-teal">upload_file</span>
          </div>
          <div>
            <h3 className="text-sm font-display font-bold text-brand-navy">
              Subir factura para procesamiento inteligente
            </h3>
            <p className="text-xs text-brand-muted font-sans">
              {selection
                ? `Archivo seleccionado: ${selection.file.name} (${(selection.file.size / 1024).toFixed(0)} KB)`
                : 'Subir factura: JPG, PNG, WEBP o PDF de hasta 10 MB'}
            </p>
          </div>
        </div>

        {/* Botones de acción */}
        <div className="flex flex-wrap sm:flex-nowrap items-center gap-2.5">
          <input
            ref={inputRef}
            type="file"
            accept={UPLOAD_ACCEPTED_TYPES.join(',')}
            onChange={handleFileChange}
            className="hidden"
          />
          <button
            onClick={() => inputRef.current?.click()}
            disabled={readOnly || processing}
            className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white border border-brand-border hover:bg-slate-50 hover:border-slate-300 rounded-lg transition-colors shadow-2xs disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-outlined text-[16px] text-brand-muted">attach_file</span>
            <span>{selection ? 'Cambiar archivo' : 'Elegir archivo'}</span>
          </button>
          
          <button
            onClick={submit}
            disabled={readOnly || processing || !selection || phase === 'done'}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-brand-navy hover:bg-brand-steel rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processing ? (
              <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
            ) : (
              <span className="material-symbols-outlined text-[16px] text-brand-teal">memory</span>
            )}
            <span>
              {processing ? 'Procesando...' : phase === 'error' && selection ? 'Reintentar' : 'Procesar factura'}
            </span>
          </button>
        </div>
      </div>

      {readOnly && (
        <Notice>Modo demostración: la subida se habilita cuando la API responde.</Notice>
      )}

      {processing && (
        <p className="text-[11px] text-brand-muted flex items-center gap-1.5 pt-1">
          <span className="w-2 h-2 rounded-full bg-brand-teal animate-ping"></span>
          Leyendo la factura con Gemini y evaluando las 4 capas de gobernanza...
        </p>
      )}

      {phase === 'error' && error && (
        <Notice tone="error">{error}</Notice>
      )}

      {phase === 'done' && invoice && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-3.5 py-2.5 rounded-lg bg-slate-50 border border-brand-border text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={invoice.decision_status} />
            <span className="font-mono font-bold text-brand-navy">{invoiceRef(invoice)}</span>
            <span className="text-brand-steel">{invoice.vendor_name || 'Proveedor sin leer'}</span>
            <span className="font-mono text-brand-navy font-semibold">${(invoice.usd_amount ?? 0).toFixed(2)} USD</span>
            {result.duplicate && (
              <span className="text-[11px] text-brand-muted font-sans">(ya se había procesado con esta solicitud)</span>
            )}
          </div>
          <button
            onClick={() => onOpenInvoice && onOpenInvoice(invoice)}
            className="self-start sm:self-auto px-3 py-1 rounded-lg bg-white border border-brand-border text-[11px] font-semibold text-brand-navy hover:bg-slate-100 transition-colors"
          >
            Ver detalle
          </button>
        </div>
      )}
    </div>
  )
}
