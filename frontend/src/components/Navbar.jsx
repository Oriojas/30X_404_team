import React from 'react'

export default function Navbar() {
  return (
    <header className="bg-[#04243C] text-white px-6 py-4 shadow-md flex justify-between items-center">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-[#2B9CAE] flex items-center justify-center font-bold text-white shadow-sm">
          B
        </div>
        <div>
          <span className="font-semibold text-xl tracking-tight">Blinka PayAgent</span>
          <span className="ml-2 text-xs bg-slate-800 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800/50">
            v4.0
          </span>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <span className="text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Railway All-in-One
        </span>
        <span className="text-xs text-slate-300 hidden sm:inline">Hackathon 30X | Equipo 404</span>
      </div>
    </header>
  )
}
