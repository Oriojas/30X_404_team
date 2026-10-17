import React from 'react'

export default function AuditDrawer({ invoice, onClose, onApproveHuman, onRejectHuman }) {
  if (!invoice) return null

  const isScaled = invoice.decision_status === 'SCALED_TO_HUMAN'
  const isApproved = invoice.decision_status === 'AUTO_APPROVED'
  const isRejected = invoice.decision_status === 'REJECTED'

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#04243C]/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Container (480px) */}
      <div className="relative w-full max-w-lg bg-white shadow-2xl z-10 flex flex-col h-full border-l border-brand-border">
        {/* Drawer Header */}
        <div className="p-5 sm:p-6 bg-brand-navy text-white flex items-center justify-between border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-teal flex items-center justify-center text-white shadow-sm">
              <span className="material-symbols-outlined text-[22px]">policy</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-cyan-300">
                  {invoice.invoice_number ? `#BLK-${invoice.invoice_number}` : `#BLK-${invoice.id}`}
                </span>
                <span className="text-slate-400 text-xs">•</span>
                <span className="text-xs text-slate-300 font-sans">Inspector de Decisión</span>
              </div>
              <h3 className="font-display font-bold text-base text-white truncate max-w-xs">
                {invoice.vendor_name}
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Cerrar inspector"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Drawer Content */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6 bg-brand-bg">
          {/* Status Banner */}
          <div className="p-4 rounded-xl border bg-white shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-brand-muted font-medium">Estado Algorítmico</span>
              {isApproved && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono text-xs font-bold">
                  <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></span>
                  AUTO_APPROVED
                </span>
              )}
              {isScaled && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-mono text-xs font-bold">
                  <span className="w-2 h-2 rounded-full bg-[#F59E0B]"></span>
                  SCALED_TO_HUMAN
                </span>
              )}
              {isRejected && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-50 text-red-800 border border-red-200 font-mono text-xs font-bold">
                  <span className="w-2 h-2 rounded-full bg-[#EF4444]"></span>
                  REJECTED
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2 font-mono text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 border border-brand-border/60">
                <span className="text-[10px] text-brand-muted block font-sans">Monto Original</span>
                <span className="font-bold text-brand-navy">
                  {invoice.original_amount?.toLocaleString()} {invoice.original_currency}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-brand-border/60">
                <span className="text-[10px] text-brand-muted block font-sans">Monto Convertido USD</span>
                <span className="font-bold text-brand-teal text-sm">
                  ${invoice.usd_amount?.toFixed(2)} USD
                </span>
              </div>
            </div>
          </div>

          {/* Rastro de Explicabilidad Caja Blanca */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-brand-steel uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-brand-teal text-[16px]">visibility</span>
              Explicabilidad Algorítmica (Caja Blanca)
            </h4>
            <div className="p-4 rounded-xl bg-white border border-brand-border text-xs text-brand-navy leading-relaxed shadow-sm">
              {invoice.audit_explanation}
            </div>
          </div>

          {/* Módulo Especial FX: $0.00 FX Markup */}
          <div className="p-4 rounded-xl bg-slate-900 text-white space-y-3 shadow-sm border border-slate-800 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-cyan-300 font-bold flex items-center gap-1 text-[11px]">
                <span className="material-symbols-outlined text-[15px]">currency_exchange</span>
                Blinka FX Zero-Markup Engine
              </span>
              <span className="px-2 py-0.5 rounded bg-brand-teal/20 text-cyan-300 text-[10px] border border-cyan-500/30">
                $0.00 Comisión
              </span>
            </div>

            <div className="space-y-1.5 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span>Moneda de Factura:</span>
                <span className="font-bold text-white">{invoice.original_currency}</span>
              </div>
              <div className="flex justify-between">
                <span>Tasa de Referencia:</span>
                <span className="text-white">
                  {invoice.original_currency === 'COP' ? '1 USD = 4,200.00 COP' : invoice.original_currency === 'MXN' ? '1 USD = 19.50 MXN' : '1.0000'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Spread / Markup Blinka:</span>
                <span className="text-emerald-400 font-bold">$0.00 USD (0.00%)</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-slate-800 font-bold text-white">
                <span>Cálculo Final USD:</span>
                <span className="text-cyan-300">${invoice.usd_amount?.toFixed(2)} USD</span>
              </div>
            </div>
          </div>

          {/* Matriz de 4 Capas: Desglose de Evaluación */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-brand-steel uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-brand-teal text-[16px]">checklist</span>
              Auditoría de Matriz en 4 Capas
            </h4>

            <div className="space-y-2 font-mono text-xs">
              {/* Capa 1: SARLAFT */}
              <div className="p-3 rounded-xl bg-white border border-brand-border flex items-center justify-between shadow-xs">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isRejected && invoice.audit_explanation.includes('SARLAFT') ? 'bg-red-500' : 'bg-emerald-500'}`} />
                  <span className="text-brand-steel font-sans text-xs">1. Listas Restrictivas (SARLAFT/OFAC)</span>
                </div>
                <span className="font-bold text-[11px]">
                  {isRejected && invoice.audit_explanation.includes('SARLAFT') ? 'FALLA / ALERTA' : 'APROBADO'}
                </span>
              </div>

              {/* Capa 2: Duplicados */}
              <div className="p-3 rounded-xl bg-white border border-brand-border flex items-center justify-between shadow-xs">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isRejected && invoice.audit_explanation.includes('duplicada') ? 'bg-red-500' : 'bg-emerald-500'}`} />
                  <span className="text-brand-steel font-sans text-xs">2. Integridad & Duplicados (30 días)</span>
                </div>
                <span className="font-bold text-[11px]">
                  {isRejected && invoice.audit_explanation.includes('duplicada') ? 'DUPLICADO DETECTADO' : 'ÚNICO 100%'}
                </span>
              </div>

              {/* Capa 3: Solvencia y Saldo */}
              <div className="p-3 rounded-xl bg-white border border-brand-border flex items-center justify-between shadow-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-brand-steel font-sans text-xs">3. Solvencia & Saldo Blinka</span>
                </div>
                <span className="font-bold text-[11px] text-emerald-700">DISPONIBLE ($48,250 USD)</span>
              </div>

              {/* Capa 4: Gobierno HITL - Umbral de Autonomía */}
              <div className="p-3 rounded-xl bg-white border border-brand-border flex items-center justify-between shadow-xs">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${invoice.usd_amount > 2000 ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                  <span className="text-brand-steel font-sans text-xs">4. Gobierno HITL ($2,000 USD)</span>
                </div>
                <span className="font-bold text-[11px]">
                  {invoice.usd_amount > 2000 ? 'EXCEDE ($2,000)' : 'DENTRO DE LÍMITE'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Drawer Footer con Acciones Human-in-the-Loop */}
        <div className="p-4 sm:p-5 bg-white border-t border-brand-border flex items-center justify-between gap-3">
          {isScaled ? (
            <>
              <button
                onClick={() => onRejectHuman && onRejectHuman(invoice.id)}
                className="flex-1 px-4 py-2.5 rounded-xl border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 font-semibold text-xs transition-colors shadow-xs"
              >
                Rechazar Pago
              </button>
              <button
                onClick={() => onApproveHuman && onApproveHuman(invoice.id)}
                className="flex-1 px-4 py-2.5 rounded-xl bg-brand-navy hover:bg-brand-steel text-white font-semibold text-xs transition-all shadow-sm active:scale-95"
              >
                Aprobar Pago
              </button>
            </>
          ) : (
            <button
              onClick={onClose}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-brand-navy font-semibold text-xs transition-colors"
            >
              Cerrar Inspector
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
