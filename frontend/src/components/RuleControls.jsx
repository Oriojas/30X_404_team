import React, { useState } from 'react'

export default function RuleControls({ currentRules = { max_autonomous_usd: 2000, sarlaft_check_enabled: true, duplicate_check_days: 30 }, onSave }) {
  const [maxUsd, setMaxUsd] = useState(currentRules.max_autonomous_usd)
  const [sarlaft, setSarlaft] = useState(currentRules.sarlaft_check_enabled)
  const [dupDays, setDupDays] = useState(currentRules.duplicate_check_days)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (onSave) {
      onSave({
        max_autonomous_usd: Number(maxUsd),
        sarlaft_check_enabled: sarlaft,
        duplicate_check_days: Number(dupDays)
      })
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
      <h2 className="text-lg font-bold text-slate-800 mb-1">Gobernanza & Reglas de Negocio</h2>
      <p className="text-xs text-slate-500 mb-4">Ajuste de parámetros de autonomía y seguridad de pagos en tiempo real</p>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
            Límite Autónomo (USD)
          </label>
          <div className="relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              $
            </div>
            <input
              type="number"
              value={maxUsd}
              onChange={(e) => setMaxUsd(e.target.value)}
              className="w-full pl-7 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-[#2B9CAE] focus:border-[#2B9CAE]"
            />
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">Pagos superiores se escalan a Telegram</span>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
            Ventana Duplicados (Días)
          </label>
          <input
            type="number"
            value={dupDays}
            onChange={(e) => setDupDays(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-[#2B9CAE] focus:border-[#2B9CAE]"
          />
          <span className="text-[11px] text-slate-400 mt-1 block">Filtro de integridad contra doble cobro</span>
        </div>

        <div className="flex flex-col justify-between">
          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
              Validación SARLAFT / Listas
            </label>
            <label className="flex items-center space-x-2 cursor-pointer mt-2">
              <input
                type="checkbox"
                checked={sarlaft}
                onChange={(e) => setSarlaft(e.target.checked)}
                className="w-4 h-4 text-[#2B9CAE] rounded border-slate-300 focus:ring-[#2B9CAE]"
              />
              <span className="text-sm text-slate-700 font-medium">Bloqueo automático de listas restrictivas</span>
            </label>
          </div>
          <button
            type="submit"
            className="mt-4 w-full bg-[#04243C] hover:bg-[#1D3557] text-white text-xs font-semibold uppercase tracking-wider py-2.5 px-4 rounded-lg transition-colors"
          >
            Guardar Reglas
          </button>
        </div>
      </form>
    </div>
  )
}
