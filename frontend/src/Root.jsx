import React, { useEffect, useState } from 'react'
import App from './App.jsx'
import PitchDeck from './components/PitchDeck.jsx'

const isPitchHash = () => window.location.hash.startsWith('#/pitch')
const isStitchHash = () => window.location.hash.startsWith('#/stitch')

/**
 * Enrutador mínimo por hash (sin dependencias; Nginx ya sirve index.html como fallback).
 *   #/pitch[/N]  -> Presentación comercial
 *   #/stitch     -> Showcase de animaciones interactivo de Stitch MCP
 *   cualquier otro -> Landing + Dashboard
 */
export default function Root() {
  const [route, setRoute] = useState(() => {
    if (isPitchHash()) return 'pitch'
    if (isStitchHash()) return 'stitch'
    return 'app'
  })

  useEffect(() => {
    const onHashChange = () => {
      if (isPitchHash()) {
        setRoute('pitch')
      } else if (isStitchHash()) {
        setRoute('stitch')
      } else {
        setRoute('app')
        const id = window.location.hash.replace('#', '')
        if (id) {
          setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }), 50)
        } else {
          window.scrollTo(0, 0)
        }
      }
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  if (route === 'stitch') {
    return (
      <div className="fixed inset-0 bg-[#04243C] z-50 flex flex-col">
        <div className="h-10 bg-[#021524] border-b border-[#1E476B] flex items-center justify-between px-4 text-xs font-mono text-cyan-300">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            STITCH MCP SHOWCASE — LABORATORIO DE ANIMACIONES
          </span>
          <div className="flex items-center gap-4">
            <a href="/stitch_showcase.html" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
              Abrir pestaña completa ↗
            </a>
            <a href="#/pitch" className="text-white hover:text-cyan-300 transition-colors font-sans">
              ← Volver al Pitch
            </a>
          </div>
        </div>
        <iframe src="/stitch_showcase.html" className="w-full flex-1 border-0" title="Stitch Animation Showcase" />
      </div>
    )
  }

  return route === 'pitch' ? <PitchDeck /> : <App />
}
