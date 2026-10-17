import React from 'react'

// Aviso compartido (modo demostración, errores y confirmaciones)
const TONES = {
  warning: { box: 'bg-amber-50 border-amber-200 text-amber-900', icon: 'text-amber-600' },
  error: { box: 'bg-red-50 border-red-200 text-red-700', icon: 'text-red-600' },
  success: { box: 'bg-emerald-50 border-emerald-200 text-emerald-800', icon: 'text-emerald-600' }
}

// md: dentro de tarjetas (Drawer, subida) · lg: avisos de sección (reglas, Audit Log)
const SIZES = {
  md: 'gap-2 px-3 py-2 rounded-lg',
  lg: 'gap-3 px-4 py-2.5 rounded-xl'
}

export default function Notice({ tone = 'warning', size = 'md', icon, children }) {
  const t = TONES[tone]
  return (
    <div className={`flex items-start border text-xs ${SIZES[size]} ${t.box}`}>
      {icon && <span className={`material-symbols-outlined text-[18px] ${t.icon}`}>{icon}</span>}
      <div>{children}</div>
    </div>
  )
}
