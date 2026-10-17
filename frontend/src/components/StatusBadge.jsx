import React from 'react'
import { statusInfo } from '../status'

// sm/lg: dashboard · slide/slideLg: diapositivas del pitch (#/pitch)
const SIZES = {
  sm: { box: 'px-2.5 py-0.5 text-[11px] font-semibold gap-1', dot: 'w-1.5 h-1.5', icon: 'text-[13px]' },
  lg: { box: 'px-3 py-1 text-xs font-bold gap-1.5', dot: 'w-1.5 h-1.5', icon: 'text-[14px]' },
  slide: { box: 'px-3 py-1 text-[13px] font-semibold tracking-wide gap-2', dot: 'w-1.5 h-1.5', icon: 'text-[16px]' },
  slideLg: { box: 'px-4 py-1.5 text-[15px] font-semibold tracking-wide gap-2', dot: 'w-2 h-2', icon: 'text-[18px]' }
}

export default function StatusBadge({ status, size = 'sm' }) {
  const info = statusInfo(status)
  const sizing = SIZES[size] || SIZES.sm

  return (
    <span className={`inline-flex items-center rounded-full border font-mono ${sizing.box} ${info.badge}`}>
      {info.human ? (
        <span className={`material-symbols-outlined leading-none ${sizing.icon}`}>person</span>
      ) : (
        <span className={`rounded-full ${sizing.dot} ${info.dot}`}></span>
      )}
      {status}
    </span>
  )
}
