import React, { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import HeroSection from './components/HeroSection'
import AgentWorkflow from './components/AgentWorkflow'
import RuleControls from './components/RuleControls'
import AuditTable from './components/AuditTable'
import AuditDrawer from './components/AuditDrawer'
import SecurityCompliance from './components/SecurityCompliance'
import Footer from './components/Footer'
import TopographyBackground from './components/TopographyBackground'

const INITIAL_INVOICES = [
  {
    id: 1,
    invoice_number: 'BLK-8921',
    vendor_name: 'Cloudflare Inc.',
    concept: 'Infraestructura Edge DNS & CDN',
    original_amount: 420.00,
    original_currency: 'USD',
    usd_amount: 420.00,
    decision_status: 'AUTO_APPROVED',
    time: 'Hace 4 min',
    audit_explanation: 'Monto inferior al umbral autónomo de $2,000 USD. Proveedor verificado en lista blanca con 14 pagos históricos idénticos. Chequeo SARLAFT limpio y fondos disponibles en tesorería.'
  },
  {
    id: 2,
    invoice_number: 'BLK-8919',
    vendor_name: 'Oracle Systems LATAM',
    concept: 'Licenciamiento Anual Cloud DB',
    original_amount: 8450.00,
    original_currency: 'USD',
    usd_amount: 8450.00,
    decision_status: 'SCALED_TO_HUMAN',
    time: 'Hace 18 min',
    audit_explanation: 'Excede el límite autónomo de $2,000 USD ($8,450.00 USD). Se envió notificación a Telegram del gerente de finanzas con botones de aprobar o rechazar.'
  },
  {
    id: 3,
    invoice_number: 'BLK-8914',
    vendor_name: 'Global Consulting S.A.S',
    concept: 'Servicios de Asesoría Legal Corporativa',
    original_amount: 3100.00,
    original_currency: 'USD',
    usd_amount: 3100.00,
    decision_status: 'REJECTED',
    time: 'Hace 42 min',
    audit_explanation: 'ALERTA SARLAFT: Representante legal nuevo coincide con reporte preventivo en lista de Personas Expuestas Políticamente (PEP). Pago frenado automáticamente.'
  },
  {
    id: 4,
    invoice_number: 'BLK-8902',
    vendor_name: 'Google Workspace',
    concept: 'Suscripción SaaS Productividad Empresarial',
    original_amount: 184.50,
    original_currency: 'USD',
    usd_amount: 184.50,
    decision_status: 'AUTO_APPROVED',
    time: 'Hace 1 hora',
    audit_explanation: 'Recurrencia mensual validada con factura previa #BLK-7811. Conciliación automática exitosa sin discrepancias fiscales ni variaciones arancelarias.'
  },
  {
    id: 5,
    invoice_number: 'BLK-7712',
    vendor_name: 'Desarrollos Tech CDMX SA',
    concept: 'Consultoría y Desarrollo de Software',
    original_amount: 52000.00,
    original_currency: 'MXN',
    usd_amount: 2666.67,
    decision_status: 'SCALED_TO_HUMAN',
    time: 'Hace 2 horas',
    audit_explanation: 'Monto en divisa local ($52,000 MXN) convertido a tasa de referencia (19.50 MXN/USD) con $0.00 FX Markup Blinka totaliza $2,666.67 USD, superando el umbral autónomo de $2,000 USD. Escalado a Telegram.'
  },
  {
    id: 6,
    invoice_number: 'BLK-7690',
    vendor_name: 'Cloud Services LATAM SAS',
    concept: 'Mantenimiento Servidores Bogotá',
    original_amount: 1500000.00,
    original_currency: 'COP',
    usd_amount: 357.14,
    decision_status: 'AUTO_APPROVED',
    time: 'Hace 3 horas',
    audit_explanation: 'Monto de $1,500,000 COP convertido a tasa 4,200 COP/USD equivale a $357.14 USD ($0 Markup Blinka). Dentro del umbral autónomo ($2,000 USD) y validado en SARLAFT.'
  }
]

export default function App() {
  const [invoices, setInvoices] = useState(INITIAL_INVOICES)
  const [selectedInvoice, setSelectedInvoice] = useState(null)
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false)

  const [rules, setRules] = useState({
    max_autonomous_usd: 2000,
    sarlaft_check_enabled: true,
    duplicate_check_days: 30,
    min_treasury_buffer_usd: 10000
  })

  // Conexión REST con FastAPI en Railway o local
  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || ''
    if (apiBase) {
      fetch(`${apiBase}/api/invoices`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (Array.isArray(data) && data.length > 0) {
            setInvoices(data)
          }
        })
        .catch(() => {
          // Fallback resiliente: se mantienen los datos de demostración
        })

      fetch(`${apiBase}/api/rules`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data && typeof data === 'object') {
            setRules((prev) => ({ ...prev, ...data }))
          }
        })
        .catch(() => {
          // Fallback a reglas predeterminadas
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

  // Acciones Human-in-the-Loop desde el Drawer
  const handleApproveHuman = (invoiceId) => {
    setInvoices((prev) =>
      prev.map((inv) =>
        inv.id === invoiceId
          ? {
              ...inv,
              decision_status: 'AUTO_APPROVED',
              audit_explanation: `Aprobado manualmente por el gerente de finanzas en Telegram el ${new Date().toLocaleTimeString()}. Pago aprobado y registrado en el Audit Log.`
            }
          : inv
      )
    )
    setSelectedInvoice((prev) =>
      prev && prev.id === invoiceId
        ? {
            ...prev,
            decision_status: 'AUTO_APPROVED',
            audit_explanation: `Aprobado manualmente por el gerente de finanzas en Telegram el ${new Date().toLocaleTimeString()}. Pago aprobado y registrado en el Audit Log.`
          }
        : prev
    )
  }

  const handleRejectHuman = (invoiceId) => {
    setInvoices((prev) =>
      prev.map((inv) =>
        inv.id === invoiceId
          ? {
              ...inv,
              decision_status: 'REJECTED',
              audit_explanation: `Rechazado manualmente por el comité financiero el ${new Date().toLocaleTimeString()}. Factura devuelta al proveedor.`
            }
          : inv
      )
    )
    setSelectedInvoice((prev) =>
      prev && prev.id === invoiceId
        ? {
            ...prev,
            decision_status: 'REJECTED',
            audit_explanation: `Rechazado manualmente por el comité financiero el ${new Date().toLocaleTimeString()}. Factura devuelta al proveedor.`
          }
        : prev
    )
  }

  return (
    <div className="min-h-screen bg-brand-bg text-brand-navy flex flex-col font-sans selection:bg-brand-teal/20 selection:text-brand-navy relative overflow-x-hidden">
      {/* Fondo geométrico de curvas de nivel (Topografía) */}
      <TopographyBackground />

      {/* Top Fixed Navbar */}
      <Navbar onOpenDemoModal={() => setIsDemoModalOpen(true)} />

      {/* Main Sections */}
      <main className="w-full pt-16 flex-1 flex flex-col relative z-10">
        {/* Section 1: Hero & Treasury Node */}
        <HeroSection />

        {/* Section 2: Telegram Workflow & 3-Step Cognitive Process */}
        <AgentWorkflow onSelectInvoiceForInspection={(inv) => setSelectedInvoice(inv)} />

        {/* Section 3: Governance & Business Rules */}
        <RuleControls currentRules={rules} onSave={handleSaveRules} />

        {/* Section 4: Live Audit Table */}
        <AuditTable
          invoices={invoices}
          onSelectInvoice={(inv) => setSelectedInvoice(inv)}
        />

        {/* Section 5: Security Compliance & CTA */}
        <SecurityCompliance
          isModalOpen={isDemoModalOpen}
          onToggleModal={(state) => setIsDemoModalOpen(state)}
        />
      </main>

      {/* Decision Inspector Drawer (Caja Blanca) */}
      <AuditDrawer
        invoice={selectedInvoice}
        onClose={() => setSelectedInvoice(null)}
        onApproveHuman={handleApproveHuman}
        onRejectHuman={handleRejectHuman}
      />

      {/* Institutional Footer */}
      <Footer />
    </div>
  )
}
