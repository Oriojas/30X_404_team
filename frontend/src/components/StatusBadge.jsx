import React from 'react'
import { statusInfo } from '../status'

export default function StatusBadge({ status, size = 'sm' }) {
  const info = statusInfo(status)
  const sizing = size === 'lg' ? 'px-3 py-1 text-xs font-bold gap-1.5' : 'px-2.5 py-0.5 text-[11px] font-semibold gap-1'

  return (
    <span className={`inline-flex items-center rounded-full border font-mono ${sizing} ${info.badge}`}>
      {info.human ? (
        <span className="material-symbols-outlined text-[13px] leading-none">person</span>
      ) : (
        <span className={`w-1.5 h-1.5 rounded-full ${info.dot}`}></span>
      )}
      {status}
    </span>
  )
}
