import React, { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import DashboardMetrics from './components/DashboardMetrics'
import AuditTable from './components/AuditTable'
import RuleControls from './components/RuleControls'

export default function App() {
  const [invoices, setInvoices] = useState([
    {
      id: 1,
      invoice_number: 'FE-8921',
      vendor_name: 'Cloud Services LATAM SAS',
      original_amount: 1500000,
      original_currency: 'COP',
      usd_amount: 357.14,
      decision_status: 'AUTO_APPROVED',
      audit_explanation: 'Monto de $357.14 USD está dentro del límite autónomo ($2,000 USD). Proveedor validado en SARLAFT.'
    },
    {
      id: 2,
      invoice_number: 'MX-4402',
      vendor_name: 'Desarrollos Tech CDMX SA',
      original_amount: 52000,
      original_currency: 'MXN',
      usd_amount: 2736.84,
      decision_status: 'SCALED_TO_HUMAN',
      audit_explanation: 'Monto de $2,736.84 USD excede el umbral autónomo ($2,000 USD). Escalado a Telegram para aprobación en 1 clic.'
    },
    {
      id: 3,
      invoice_number: 'FE-8921',
      vendor_name: 'Cloud Services LATAM SAS',
      original_amount: 1500000,
      original_currency: 'COP',
      usd_amount: 357.14,
      decision_status: 'REJECTED',
      audit_explanation: 'Factura duplicada: el número FE-8921 ya fue procesado y pagado dentro de la ventana de 30 días.'
    }
  ])

  const [metrics, setMetrics] = useState({
    processed: 3,
    autoApproved: 1,
    scaled: 1,
    rejected: 1,
    totalUsd: 3451.12
  })

  const [rules, setRules] = useState({
    max_autonomous_usd: 2000,
    sarlaft_check_enabled: true,
    duplicate_check_days: 30
  })

  // Carga inicial desde backend si está disponible
  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || ''
    if (apiBase) {
      fetch(`${apiBase}/api/invoices`)
        .then((res) => res.ok ? res.json() : null)
        .then((data) => {
          if (data && data.length > 0) {
            setInvoices(data)
          }
        })
        .catch(() => {
          // Si el backend aún no está corriendo localmente, se mantienen los datos de demostración
        })
    }
  }, [])

  const handleSaveRules = (newRules) => {
    setRules(newRules)
    const apiBase = import.meta.env.VITE_API_BASE_URL || ''
    if (apiBase) {
      fetch(`${apiBase}/api/rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newRules)
      }).catch(console.error)
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8">
        {/* Banner de Bienvenida y Propuesta de Valor */}
        <div className="bg-gradient-to-r from-[#04243C] via-[#1D3557] to-[#04243C] rounded-2xl p-6 sm:p-8 text-white shadow-lg mb-8">
          <div className="max-w-3xl">
            <span className="text-xs uppercase tracking-widest font-bold text-[#2B9CAE] bg-[#2B9CAE]/20 px-3 py-1 rounded-full border border-[#2B9CAE]/30 inline-block mb-3">
              Hackathon 30X | Reto Blinka
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Control Autónomo & Gobernanza de Pagos Corporativos
            </h1>
            <p className="mt-2 text-sm sm:text-base text-slate-300">
              Ingesta automática vía Telegram, extracción multimodal con Gemini 1.5 Flash, $0.00 FX Markup y registro explicable en tiempo real.
            </p>
          </div>
        </div>

        {/* Métricas en Tarjetas */}
        <DashboardMetrics metrics={metrics} />

        {/* Controles de Gobernanza de Reglas */}
        <RuleControls currentRules={rules} onSave={handleSaveRules} />

        {/* Tabla de Auditoría Explicable */}
        <AuditTable invoices={invoices} />
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Blinka PayAgent &copy; 2026 — Desarrollado por Oscar Riojas & Luis Felipe Marín Giraldo
      </footer>
    </div>
  )
}
