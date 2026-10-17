import React, { useEffect, useState } from 'react'
import Notice from './Notice'
import { availableUsd, budgetUsage, formatUsd, headroomColor, headroomText, treasuryHeadroom } from '../api'

function FieldError({ message }) {
  if (!message) return null
  return <p className="text-[11px] text-red-600 font-sans">{message}</p>
}

// Campos con su propio mensaje de error en el panel; cualquier otro error del 422 va al aviso general
const RULE_FIELDS = ['max_autonomous_usd', 'max_payment_usd', 'duplicate_check_days', 'min_treasury_buffer_usd',
  'monthly_budget_usd']

export default function RuleControls({ currentRules, treasury, readOnly = false, onSave }) {
  const [maxUsd, setMaxUsd] = useState(currentRules.max_autonomous_usd)
  const [sarlaft, setSarlaft] = useState(currentRules.sarlaft_check_enabled)
  const [dupDays, setDupDays] = useState(currentRules.duplicate_check_days)
  const [bufferUsd, setBufferUsd] = useState(currentRules.min_treasury_buffer_usd)
  const [maxPaymentUsd, setMaxPaymentUsd] = useState(currentRules.max_payment_usd)
  // El presupuesto vive en la tesorería (PATCH /api/treasury), no en las reglas
  const savedBudget = treasury?.monthly_budget_usd ?? null
  const [budgetUsd, setBudgetUsd] = useState(savedBudget ?? '')
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  // Las reglas se guardaron pero el presupuesto no (segunda llamada, D15)
  const [partialSave, setPartialSave] = useState(false)
  const [fieldErrors, setFieldErrors] = useState({})
  const [generalError, setGeneralError] = useState(null)
  // La holgura sigue al valor que se está editando, antes de guardarlo
  const available = availableUsd(treasury)
  const headroom = treasuryHeadroom(available, bufferUsd)
  const budget = budgetUsage(treasury)

  // Los campos reflejan las reglas vigentes cuando llegan de la API o tras guardarlas
  const rulesKey = JSON.stringify(currentRules)
  useEffect(() => {
    setMaxUsd(currentRules.max_autonomous_usd)
    setSarlaft(currentRules.sarlaft_check_enabled)
    setDupDays(currentRules.duplicate_check_days)
    setBufferUsd(currentRules.min_treasury_buffer_usd)
    setMaxPaymentUsd(currentRules.max_payment_usd)
  }, [rulesKey]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setBudgetUsd(savedBudget ?? '')
  }, [savedBudget])

  const handleApplyChanges = async (e) => {
    if (e) e.preventDefault()
    if (!onSave || readOnly || saving) return
    const updated = {
      max_autonomous_usd: Number(maxUsd),
      sarlaft_check_enabled: sarlaft,
      duplicate_check_days: Number(dupDays),
      min_treasury_buffer_usd: Number(bufferUsd),
      max_payment_usd: Number(maxPaymentUsd)
    }
    // Solo se envía el presupuesto si cambió (y si hay tesorería que editar)
    const budgetChanged = savedBudget != null && budgetUsd !== '' && Number(budgetUsd) !== Number(savedBudget)

    setSaving(true)
    setFieldErrors({})
    setGeneralError(null)
    setPartialSave(false)
    try {
      await onSave(updated, budgetChanged ? Number(budgetUsd) : null)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2500)
    } catch (err) {
      // Si falló el presupuesto, las reglas ya quedaron guardadas: el error va junto al presupuesto
      const byField = err.step === 'budget' && !Object.keys(err.fieldErrors || {}).length
        ? { monthly_budget_usd: err.message }
        : err.fieldErrors || {}
      setPartialSave(err.step === 'budget')
      setFieldErrors(byField)
      const allShownByField = Object.keys(byField).length > 0 && Object.keys(byField).every((f) => RULE_FIELDS.includes(f))
      if (!allShownByField) setGeneralError(err.message || 'No se pudieron guardar las reglas.')
    } finally {
      setSaving(false)
    }
  }

  const handleDownloadJson = () => {
    const data = {
      policy_version: "2026.4",
      last_updated: new Date().toISOString(),
      governance_rules: {
        max_autonomous_usd: Number(maxUsd),
        sarlaft_check_enabled: sarlaft,
        duplicate_check_days: Number(dupDays),
        min_treasury_buffer_usd: Number(bufferUsd),
        max_payment_usd: Number(maxPaymentUsd),
        monthly_budget_usd: budgetUsd === '' ? null : Number(budgetUsd)
      },
      audit_protocol: "Audit Log PostgreSQL",
      rail: "Blinka Settlement Rail"
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `blinka_governance_rules_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <section className="w-full py-12 lg:py-16 bg-transparent border-b border-brand-border/60" id="reglas-gobernanza">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2 flex-1 min-w-0 pr-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-brand-teal uppercase tracking-wider">
              <span className="material-symbols-outlined text-[15px]">tune</span>
              Gobernanza Financiera
            </div>
            <h2 className="font-display font-bold text-2xl lg:text-3xl text-brand-navy tracking-tight">
              Reglas &amp; Gobernanza de Pagos
            </h2>
            <p className="text-sm text-brand-muted leading-relaxed">
              Control milimétrico sobre la autonomía del agente financiero. Tú defines los límites estrictos; la inteligencia artificial ejecuta con rigor matemático.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0 self-start sm:self-auto">
            <button
              onClick={handleDownloadJson}
              className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-xl bg-white border border-brand-border text-xs font-semibold text-brand-navy hover:bg-slate-50 transition-colors shadow-2xs whitespace-nowrap"
            >
              <span className="material-symbols-outlined text-[16px] text-brand-teal">code</span>
              <span>Descargar Políticas JSON</span>
            </button>

            <button
              onClick={handleApplyChanges}
              disabled={readOnly || saving}
              className="inline-flex items-center gap-1.5 h-9 px-4 rounded-xl bg-brand-navy hover:bg-brand-steel text-white text-xs font-semibold transition-all shadow-sm active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 whitespace-nowrap"
            >
              <span className="material-symbols-outlined text-[16px] text-brand-teal">save</span>
              <span>{saving ? 'Guardando...' : 'Guardar Políticas'}</span>
            </button>
          </div>
        </div>

        {saveSuccess && (
          <Notice tone="success" size="lg">Reglas guardadas. Las próximas facturas se evalúan con estos valores.</Notice>
        )}
        {partialSave && (
          <Notice size="lg">Las reglas se guardaron, pero el presupuesto no: corrígelo y vuelve a guardar.</Notice>
        )}
        {generalError && (
          <Notice tone="error" size="lg">{generalError}</Notice>
        )}
        {readOnly && (
          <Notice size="lg">Modo demostración: guardar reglas se habilita cuando la API responde.</Notice>
        )}

        {/* 4-Card Responsive Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch">
          {/* Card 1: Límite Máximo Autónomo */}
          <div className="bg-white rounded-xl border border-brand-border p-4 sm:p-5 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between space-y-4">
            <div className="space-y-2.5 flex-1 flex flex-col">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                  <span className="material-symbols-outlined text-[20px]">payments</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-brand-steel border border-brand-border text-[11px] font-semibold">
                  Activo
                </span>
              </div>
              <h3 className="font-display font-semibold text-base text-brand-navy">Límite Máximo Autónomo</h3>
              <p className="text-xs text-brand-muted leading-relaxed min-h-[48px]">
                Pagos superiores al umbral escalan a aprobación humana en el dashboard; Telegram solo informa el resultado.
              </p>
            </div>

            {/* Slider & Visualizer (Subtarjeta 1) */}
            <div className="p-3 rounded-xl bg-slate-50 border border-brand-border/80 h-[142px] flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs">
                <span className="text-brand-muted font-sans text-[11px]">Umbral Configurado:</span>
                <span className="font-mono font-bold text-brand-navy text-sm">${Number(maxUsd).toLocaleString()} USD</span>
              </div>

              <div className="space-y-1.5">
                <input
                  type="range"
                  min="500"
                  max="10000"
                  step="250"
                  value={maxUsd}
                  onChange={(e) => setMaxUsd(e.target.value)}
                  className="w-full accent-brand-teal cursor-pointer h-2 bg-slate-200 rounded-lg"
                />

                <div className="flex items-center justify-between font-mono text-[10px] text-brand-muted">
                  <span>$500 Min</span>
                  <span>$10,000 USD Max</span>
                </div>
              </div>
              <FieldError message={fieldErrors.max_autonomous_usd} />
            </div>

            {/* Tope duro por pago (FIN-04): por encima se rechaza, sin aprobación humana posible */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-brand-border/80 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1 text-xs font-mono">
                <span className="text-brand-muted font-sans text-[11px] whitespace-nowrap">Tope por pago:</span>
                <span className="flex items-center gap-1 font-bold text-brand-navy">
                  $
                  <input
                    type="number"
                    min="0"
                    step="500"
                    value={maxPaymentUsd ?? ''}
                    onChange={(e) => setMaxPaymentUsd(e.target.value)}
                    aria-label="Tope máximo por pago en USD"
                    className={`w-24 bg-white border rounded px-2 py-0.5 text-xs text-brand-navy font-mono text-right ${fieldErrors.max_payment_usd ? 'border-red-400' : 'border-brand-border'}`}
                  />
                  USD
                </span>
              </div>
              <p className="text-[10px] text-brand-muted leading-snug">Por encima se rechaza (FIN-04). No puede ser menor que el umbral.</p>
              <FieldError message={fieldErrors.max_payment_usd} />
            </div>
          </div>

          {/* Card 2: Validación SARLAFT & OFAC */}
          <div className="bg-white rounded-xl border border-brand-border p-4 sm:p-5 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between space-y-4">
            <div className="space-y-2.5 flex-1 flex flex-col">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                  <span className="material-symbols-outlined text-[20px]">shield</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-semibold">
                  {sarlaft ? 'Estricto 100%' : 'Desactivado'}
                </span>
              </div>
              <h3 className="font-display font-semibold text-base text-brand-navy">Validación SARLAFT &amp; OFAC</h3>
              <p className="text-xs text-brand-muted leading-relaxed min-h-[48px]">
                Cruce automático de contrapartes y beneficiarios en listas restrictivas antes de aprobar el pago.
              </p>
            </div>

            {/* Toggle Switch & Telemetry (Subtarjeta 2) */}
            <div className="p-3 rounded-xl bg-slate-50 border border-brand-border/80 h-[142px] flex flex-col justify-between font-mono text-xs">
              <div className="flex items-center justify-between pb-1 border-b border-brand-border/60">
                <span className="text-brand-muted font-sans text-[11px]">Estado del Filtro</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={sarlaft}
                    onChange={(e) => setSarlaft(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand-teal"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Listas PEP / ONU:</span>
                <span className="text-brand-teal font-semibold text-[11px]">Activo</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Cobertura:</span>
                <span className="text-brand-navy font-semibold text-[10px] tracking-tight">OFAC · ONU · GAFI</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Bloqueo:</span>
                <span className="text-brand-steel font-bold text-[11px]">Inmediato</span>
              </div>
            </div>
          </div>

          {/* Card 3: Deduplicación */}
          <div className="bg-white rounded-xl border border-brand-border p-4 sm:p-5 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between space-y-4">
            <div className="space-y-2.5 flex-1 flex flex-col">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                  <span className="material-symbols-outlined text-[20px]">fingerprint</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-brand-steel border border-brand-border text-[11px] font-semibold">
                  ID + Proveedor
                </span>
              </div>
              <h3 className="font-display font-semibold text-base text-brand-navy">Detección de Duplicados</h3>
              <p className="text-xs text-brand-muted leading-relaxed min-h-[48px]">
                Compara número de factura y proveedor (o monto y proveedor) dentro de la ventana configurada para evitar dobles pagos automáticos.
              </p>
            </div>

            {/* Select Window & Telemetry (Subtarjeta 3) */}
            <div className="p-3 rounded-xl bg-slate-50 border border-brand-border/80 h-[142px] flex flex-col justify-between font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Ventana:</span>
                <span className="flex items-center gap-1 font-sans text-xs">
                  <input
                    type="number"
                    value={dupDays}
                    onChange={(e) => setDupDays(e.target.value)}
                    aria-label="Ventana de duplicados en días"
                    className={`w-12 bg-white border rounded px-1.5 py-0.5 text-xs text-brand-navy font-mono text-right ${fieldErrors.duplicate_check_days ? 'border-red-400' : 'border-brand-border'}`}
                  />
                  <span className="text-brand-muted text-[11px]">días</span>
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Criterio:</span>
                <span className="text-brand-navy font-semibold text-[11px]">ID + Proveedor</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Acción:</span>
                <span className="text-emerald-700 font-semibold text-[11px]">Rechazo automático</span>
              </div>
              <FieldError message={fieldErrors.duplicate_check_days} />
            </div>
          </div>

          {/* Card 4: Colchón de Tesorería */}
          <div className="bg-white rounded-xl border border-brand-border p-4 sm:p-5 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between space-y-4">
            <div className="space-y-2.5 flex-1 flex flex-col">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                  <span className="material-symbols-outlined text-[20px]">account_balance_wallet</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-brand-steel border border-brand-border text-[11px] font-semibold">
                  Seguridad
                </span>
              </div>
              <h3 className="font-display font-semibold text-base text-brand-navy">Colchón Mínimo Tesorería</h3>
              <p className="text-xs text-brand-muted leading-relaxed min-h-[48px]">
                Escala a un humano los pagos si la liquidez proyectada cae por debajo de la reserva mínima protegida.
              </p>
            </div>

            {/* Bottom Reserve Block (Subtarjeta 4) */}
            <div className="p-3 rounded-xl bg-slate-50 border border-brand-border/80 h-[142px] flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs">
                <span className="text-brand-muted font-sans text-[11px]">Reserva Mínima:</span>
                <div className="flex items-center gap-1 font-mono text-xs font-bold text-brand-navy">
                  <span className="text-slate-400">$</span>
                  <input
                    type="number"
                    value={bufferUsd}
                    onChange={(e) => setBufferUsd(e.target.value)}
                    aria-label="Reserva mínima de tesorería en USD"
                    className={`w-14 bg-white border rounded px-1.5 py-0.5 text-xs text-brand-navy font-mono text-right ${fieldErrors.min_treasury_buffer_usd ? 'border-red-400' : 'border-brand-border'}`}
                  />
                  <span className="text-[10px] text-slate-500 font-sans font-normal">USD</span>
                </div>
              </div>

              <div className="space-y-1">
                <div className="relative w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="bg-brand-teal h-full rounded-full transition-all duration-500" style={{ width: `${headroom?.pct ?? 0}%` }}></div>
                </div>

                <div className="flex items-center justify-between font-mono text-[10px] text-brand-steel">
                  <span>Disponible: {available != null ? `${formatUsd(available)}` : '—'}</span>
                  <span className={`font-semibold ${headroomColor(headroom)}`}>
                    Holgura {headroomText(headroom)}
                  </span>
                </div>
              </div>
              <FieldError message={fieldErrors.min_treasury_buffer_usd} />
            </div>
          </div>
        </div>

        {/* Presupuesto del período (FIN-02): se guarda con PATCH /api/treasury, sin mover la foto del saldo */}
        <div className="mt-6 bg-white rounded-xl border border-brand-border p-5 sm:p-6 shadow-sm flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                <span className="material-symbols-outlined text-[20px]">calendar_month</span>
              </div>
              <div>
                <h3 className="font-display font-semibold text-base text-brand-navy">Presupuesto del Período</h3>
                <p className="text-xs text-brand-muted">Escala a un humano los pagos que superan lo que queda del presupuesto mensual (FIN-02).</p>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-brand-steel border border-brand-border text-[11px] font-semibold">
              Solvencia
            </span>
          </div>

          <div className="relative w-full h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${budget && !budget.ok ? 'bg-red-500' : 'bg-brand-teal'}`}
              style={{ width: `${budget?.pct ?? 0}%` }}
            ></div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 font-mono text-xs items-center">
            <span className="text-brand-steel flex flex-wrap items-center gap-1">
              Presupuesto mensual:
              {savedBudget != null ? (
                <span className="flex items-center gap-1 font-bold text-brand-navy">
                  $
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    value={budgetUsd}
                    onChange={(e) => setBudgetUsd(e.target.value)}
                    aria-label="Presupuesto mensual en USD"
                    className={`w-28 bg-white border rounded px-2 py-0.5 text-xs text-brand-navy font-mono text-right ${fieldErrors.monthly_budget_usd ? 'border-red-400' : 'border-brand-border'}`}
                  />
                  USD
                </span>
              ) : (
                <strong className="text-brand-navy">—</strong>
              )}
            </span>
            <span className="text-brand-steel sm:text-center">Gasto aprobado del mes: <strong className="text-brand-navy">{budget ? `${formatUsd(budget.spent)} USD` : '—'}</strong></span>
            <span className={`sm:text-right font-semibold ${budget ? (budget.ok ? 'text-emerald-700' : 'text-red-600') : 'text-brand-muted'}`}>
              Restante: {budget ? `${formatUsd(Math.max(0, budget.remaining))} USD` : '—'}
            </span>
          </div>
          <FieldError message={fieldErrors.monthly_budget_usd} />
        </div>
      </div>
    </section>
  )
}
