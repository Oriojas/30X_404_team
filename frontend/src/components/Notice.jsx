import React from 'react'

// Aviso compartido (modo demostración, errores y confirmaciones)
const TONES = {
  warning: 'bg-amber-50 border-amber-200 text-amber-900',
  error: 'bg-red-50 border-red-200 text-red-700',
  success: 'bg-emerald-50 border-emerald-200 text-emerald-800'
}

export default function Notice({ tone = 'warning', icon, children }) {
  return (
    <div className={`flex items-start gap-2 px-3 py-2 rounded-lg border text-xs ${TONES[tone]}`}>
      {icon && <span className="material-symbols-outlined text-[18px]">{icon}</span>}
      <div>{children}</div>
    </div>
  )
}
