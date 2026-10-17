import React, { useEffect, useState } from 'react'
import App from './App.jsx'
import PitchDeck from './components/PitchDeck.jsx'

const isPitchHash = () => window.location.hash.startsWith('#/pitch')

/**
 * Enrutador mínimo por hash (sin dependencias; Nginx ya sirve index.html como fallback).
 *   #/pitch[/N]  -> Presentación comercial
 *   cualquier otro -> Landing + Dashboard
 */
export default function Root() {
  const [showPitch, setShowPitch] = useState(isPitchHash)

  useEffect(() => {
    const onHashChange = () => {
      const pitch = isPitchHash()
      setShowPitch(pitch)

      // Al volver desde la presentación a un ancla de la landing (ej. #auditoria), hacer scroll tras montar.
      if (!pitch) {
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

  return showPitch ? <PitchDeck /> : <App />
}
