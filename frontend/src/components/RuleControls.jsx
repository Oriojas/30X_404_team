import React, { useState } from 'react'

export default function RuleControls({
  currentRules = {
    max_autonomous_usd: 2000,
    sarlaft_check_enabled: true,
    duplicate_check_days: 30,
    min_treasury_buffer_usd: 10000
  },
  onSave
}) {
  const [maxUsd, setMaxUsd] = useState(currentRules.max_autonomous_usd || 2000)
  const [sarlaft, setSarlaft] = useState(currentRules.sarlaft_check_enabled ?? true)
  const [dupDays, setDupDays] = useState(currentRules.duplicate_check_days || 30)
  const [bufferUsd] = useState(currentRules.min_treasury_buffer_usd || 10000)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const handleApplyChanges = (e) => {
    if (e) e.preventDefault()
    const updated = {
      max_autonomous_usd: Number(maxUsd),
      sarlaft_check_enabled: sarlaft,
      duplicate_check_days: Number(dupDays),
      min_treasury_buffer_usd: Number(bufferUsd)
    }

    if (onSave) {
      onSave(updated)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2500)
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
        min_treasury_buffer_usd: Number(bufferUsd)
      },
      audit_protocol: "SHA-256 Strict Ledger",
      rail: "Blinka Multi-rail Zero-Markup Engine"
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
    <section className="w-full py-12 lg:py-16 bg-brand-bg border-b border-brand-border" id="reglas-gobernanza">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="max-w-2xl space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-brand-teal uppercase tracking-wider">
              <span className="material-symbols-outlined text-[15px]">tune</span>
              Gobernanza Financiera
            </div>
            <h2 className="font-display font-bold text-2xl lg:text-3xl text-brand-navy tracking-tight">
              Reglas & Gobernanza de Pagos
            </h2>
            <p className="text-sm text-brand-muted leading-relaxed">
              Control milimétrico sobre la autonomía del agente financiero. Tú defines los límites estrictos; la inteligencia artificial ejecuta con rigor matemático.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start md:self-auto flex-wrap">
            <button
              onClick={handleDownloadJson}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-brand-border text-xs font-semibold text-brand-navy hover:bg-slate-50 transition-colors shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px] text-brand-teal">code</span>
              <span>Descargar Políticas JSON</span>
            </button>

            <button
              onClick={handleApplyChanges}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-navy hover:bg-brand-steel text-white text-xs font-semibold transition-all shadow-sm active:scale-95"
            >
              <span className="material-symbols-outlined text-[16px] text-brand-teal">save</span>
              <span>{saveSuccess ? '¡Políticas Guardadas!' : 'Guardar Políticas'}</span>
            </button>
          </div>
        </div>

        {/* 4-Card Responsive Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch">
          {/* Card 1: Límite Máximo Autónomo */}
          <div className="bg-white rounded-xl border border-brand-border p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between space-y-5">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                  <span className="material-symbols-outlined text-[20px]">payments</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-brand-steel border border-brand-border text-[11px] font-semibold">
                  Activo
                </span>
              </div>
              <h3 className="font-display font-semibold text-base text-brand-navy">Límite Máximo Autónomo</h3>
              <p className="text-xs text-brand-muted leading-relaxed">
                Pagos superiores al umbral escalan inmediatamente a aprobación biométrica 2FA del CFO en Telegram.
              </p>
            </div>

            {/* Slider & Visualizer */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-brand-border/80 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-brand-muted font-medium">Umbral Configurado:</span>
                <span className="font-mono font-bold text-brand-navy text-sm">${Number(maxUsd).toLocaleString()} USD</span>
              </div>

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
          </div>

          {/* Card 2: Validación SARLAFT & OFAC */}
          <div className="bg-white rounded-xl border border-brand-border p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between space-y-5">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                  <span className="material-symbols-outlined text-[20px]">shield</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-semibold">
                  {sarlaft ? 'Estricto 100%' : 'Desactivado'}
                </span>
              </div>
              <h3 className="font-display font-semibold text-base text-brand-navy">Validación SARLAFT & OFAC</h3>
              <p className="text-xs text-brand-muted leading-relaxed">
                Cruce automático e instantáneo de contrapartes, socios y beneficiarios finales en listas restrictivas antes del desembolso.
              </p>
            </div>

            {/* Toggle Switch & Telemetry */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-brand-border/80 space-y-2 font-mono text-xs">
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
                <span className="text-brand-teal font-semibold">100% ONLINE</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Latencia Consulta:</span>
                <span className="text-brand-navy font-semibold">84ms</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Bloqueo Preventivo:</span>
                <span className="text-brand-steel font-bold">Inmediato</span>
              </div>
            </div>
          </div>

          {/* Card 3: Deduplicación Criptográfica */}
          <div className="bg-white rounded-xl border border-brand-border p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between space-y-5">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                  <span className="material-symbols-outlined text-[20px]">fingerprint</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-brand-steel border border-brand-border text-[11px] font-semibold">
                  SHA-256 Hash
                </span>
              </div>
              <h3 className="font-display font-semibold text-base text-brand-navy">Detección de Duplicados</h3>
              <p className="text-xs text-brand-muted leading-relaxed">
                Compara el hash SHA-256 del documento fiscal, folio y beneficiario para evitar dobles pagos automáticos.
              </p>
            </div>

            {/* Select Window & Telemetry */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-brand-border/80 space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Ventana de Memoria:</span>
                <select
                  value={dupDays}
                  onChange={(e) => setDupDays(Number(e.target.value))}
                  className="bg-white border border-brand-border rounded px-2 py-0.5 text-xs text-brand-navy font-mono"
                >
                  <option value={15}>15 días</option>
                  <option value={30}>30 días</option>
                  <option value={60}>60 días</option>
                  <option value={90}>90 días</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Algoritmo Hash:</span>
                <span className="text-brand-navy font-semibold">SHA-256</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-brand-muted font-sans text-[11px]">Falsos Positivos:</span>
                <span className="text-emerald-700 font-semibold">0.00%</span>
              </div>
            </div>
          </div>

          {/* Card 4: Colchón de Tesorería */}
          <div className="bg-white rounded-xl border border-brand-border p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between space-y-5">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-brand-teal">
                  <span className="material-symbols-outlined text-[20px]">account_balance_wallet</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-brand-steel border border-brand-border text-[11px] font-semibold">
                  Seguridad
                </span>
              </div>
              <h3 className="font-display font-semibold text-base text-brand-navy">Colchón Mínimo Tesorería</h3>
              <p className="text-xs text-brand-muted leading-relaxed">
                Pausa automática de dispersiones si la liquidez proyectada cae por debajo de la reserva mínima protegida.
              </p>
            </div>

            {/* Bottom Reserve Block */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-brand-border/80 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-brand-muted font-sans text-[11px]">Reserva Protegida:</span>
                <span className="font-bold text-brand-navy">${Number(bufferUsd).toLocaleString()} USD</span>
              </div>

              <div className="relative w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                <div className="bg-brand-teal h-full rounded-full" style={{ width: '79%' }}></div>
              </div>

              <div className="flex items-center justify-between font-mono text-[10px] text-brand-steel">
                <span>Caja: $48,250 USD</span>
                <span className="text-emerald-700 font-semibold">Holgura 79% OK</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
