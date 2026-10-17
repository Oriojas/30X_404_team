import React, { useState, useEffect, useCallback, useRef } from 'react'
import Navbar from './components/Navbar'
import HeroSection from './components/HeroSection'
import AgentWorkflow from './components/AgentWorkflow'
import RuleControls from './components/RuleControls'
import AuditTable from './components/AuditTable'
import AuditDrawer from './components/AuditDrawer'
import InvoiceUpload from './components/InvoiceUpload'
import SecurityCompliance from './components/SecurityCompliance'
import Footer from './components/Footer'
import TopographyBackground from './components/TopographyBackground'
import { listInvoices, getRules, getTreasury, decideInvoice, saveRules, DEFAULT_RULES, DEFAULT_TREASURY } from './api'

// Datos de demostración (misma forma que InvoiceResponse): solo se muestran si la API no responde.
const minutesAgo = (m) => new Date(Date.now() - m * 60000).toISOString()

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
    processed_at: minutesAgo(4),
    channel_source: 'TELEGRAM',
    evaluations: {},
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
    processed_at: minutesAgo(18),
    channel_source: 'TELEGRAM',
    evaluations: {},
    audit_explanation: 'Excede el límite autónomo de $2,000 USD ($8,450.00 USD). Escalado al aprobador financiero para su decisión en el dashboard.'
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
    processed_at: minutesAgo(42),
    channel_source: 'TELEGRAM',
    evaluations: {},
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
    processed_at: minutesAgo(60),
    channel_source: 'TELEGRAM',
    evaluations: {},
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
    fx_rate_applied: 19.5,
    decision_status: 'SCALED_TO_HUMAN',
    processed_at: minutesAgo(120),
    channel_source: 'TELEGRAM',
    evaluations: {},
    audit_explanation: 'Monto en divisa local ($52,000 MXN) convertido a tasa de referencia (19.50 MXN/USD) con $0.00 FX Markup Blinka totaliza $2,666.67 USD, superando el umbral autónomo de $2,000 USD. Escalado al aprobador financiero.'
  },
  {
    id: 6,
    invoice_number: 'BLK-7690',
    vendor_name: 'Cloud Services LATAM SAS',
    concept: 'Mantenimiento Servidores Bogotá',
    original_amount: 1500000.00,
    original_currency: 'COP',
    usd_amount: 357.14,
    fx_rate_applied: 4200,
    decision_status: 'AUTO_APPROVED',
    processed_at: minutesAgo(180),
    channel_source: 'TELEGRAM',
    evaluations: {},
    audit_explanation: 'Monto de $1,500,000 COP convertido a tasa 4,200 COP/USD equivale a $357.14 USD ($0 Markup Blinka). Dentro del umbral autónomo ($2,000 USD) y validado en SARLAFT.'
  }
]

export default function App() {
  const [invoices, setInvoices] = useState([])
  const [loadingInvoices, setLoadingInvoices] = useState(true)
  // null mientras carga la primera vez; false = modo demostración
  const [apiAvailable, setApiAvailable] = useState(null)
  // Un refresco fallido después de cargar datos reales no los reemplaza por los de demostración
  const hasRealData = useRef(false)
  const [refreshError, setRefreshError] = useState(null)
  const [selectedInvoice, setSelectedInvoice] = useState(null)
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false)

  const [rules, setRules] = useState(DEFAULT_RULES)
  // null hasta que responde GET /api/treasury; si falla con la API viva se muestra "—", no el saldo del seed
  const [treasury, setTreasury] = useState(null)
  const shownTreasury = treasury ?? (apiAvailable === false ? DEFAULT_TREASURY : null)

  // Lo comprometido cambia con cada aprobación: se relee tras subir, decidir o refrescar.
  // Solo cuenta la respuesta de la última lectura: una más lenta de antes no pisa una más nueva.
  const treasuryRequest = useRef(0)
  const loadTreasury = useCallback(() => {
    const requestId = ++treasuryRequest.current
    getTreasury()
      .then((data) => {
        if (requestId === treasuryRequest.current && data && typeof data === 'object') setTreasury(data)
      })
      .catch(() => {
        // Sin tesorería: el hero y la tarjeta muestran "—" (o el seed en modo demostración);
        // un refresco fallido conserva el último valor leído
      })
  }, [])

  // Con la API disponible se muestran siempre los datos reales, aunque la lista esté vacía
  const loadInvoices = useCallback(async () => {
    setLoadingInvoices(true)
    try {
      const data = await listInvoices()
      setInvoices(data)
      // El Drawer abierto refleja el estado vigente (p. ej. tras un 409)
      setSelectedInvoice((prev) => (prev ? data.find((inv) => inv.id === prev.id) || prev : prev))
      setApiAvailable(true)
      setRefreshError(null)
      hasRealData.current = true
    } catch (err) {
      if (hasRealData.current) {
        setRefreshError(err.message)
      } else {
        setInvoices(INITIAL_INVOICES)
        setApiAvailable(false)
      }
    } finally {
      setLoadingInvoices(false)
    }
  }, [])

  useEffect(() => {
    loadInvoices()
    getRules()
      .then((data) => {
        if (data && typeof data === 'object') {
          setRules((prev) => ({ ...prev, ...data }))
        }
      })
      .catch(() => {
        // Fallback a reglas predeterminadas
      })
    loadTreasury()
  }, [loadInvoices, loadTreasury])

  // Las reglas locales solo cambian con la respuesta de la API; un error (p. ej. 422) sube al panel
  const handleSaveRules = async (newRules) => {
    const saved = await saveRules(newRules)
    setRules((prev) => ({ ...prev, ...saved }))
    return saved
  }

  // Reemplaza (o agrega al inicio) una factura devuelta por la API
  const upsertInvoice = useCallback((invoice) => {
    setInvoices((prev) =>
      prev.some((inv) => inv.id === invoice.id)
        ? prev.map((inv) => (inv.id === invoice.id ? invoice : inv))
        : [invoice, ...prev]
    )
    setSelectedInvoice((prev) => (prev && prev.id === invoice.id ? invoice : prev))
  }, [])

  // Decisión humana (solo en el dashboard). Un 409 significa que otra persona ya decidió:
  // se recarga el listado y el error sube al Drawer para mostrar el mensaje.
  const handleDecide = async (invoiceId, decision, note) => {
    try {
      upsertInvoice(await decideInvoice(invoiceId, decision, note))
      loadTreasury()
    } catch (err) {
      if (err.status === 409) loadInvoices()
      throw err
    }
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
        <HeroSection treasury={shownTreasury} rules={rules} />

        {/* Section 2: Telegram Workflow & 3-Step Cognitive Process */}
        <AgentWorkflow onSelectInvoiceForInspection={(inv) => setSelectedInvoice(inv)} />

        {/* Section 3: Governance & Business Rules */}
        <RuleControls
          currentRules={rules}
          treasury={shownTreasury}
          readOnly={apiAvailable === false}
          onSave={handleSaveRules}
        />

        {/* Section 4: Live Audit Table */}
        <AuditTable
          invoices={invoices}
          loading={loadingInvoices}
          demoMode={apiAvailable === false}
          refreshError={refreshError}
          onRefresh={() => {
            loadInvoices()
            loadTreasury()
          }}
          onSelectInvoice={(inv) => setSelectedInvoice(inv)}
        >
          <InvoiceUpload
            readOnly={apiAvailable === false}
            onUploaded={(invoice) => {
              upsertInvoice(invoice)
              loadTreasury()
            }}
            onOpenInvoice={(inv) => setSelectedInvoice(inv)}
          />
        </AuditTable>

        {/* Section 5: Security Compliance & CTA */}
        <SecurityCompliance
          isModalOpen={isDemoModalOpen}
          onToggleModal={(state) => setIsDemoModalOpen(state)}
        />
      </main>

      {/* Decision Inspector Drawer (Caja Blanca) */}
      <AuditDrawer
        key={selectedInvoice?.id}
        invoice={selectedInvoice}
        readOnly={apiAvailable === false}
        onClose={() => setSelectedInvoice(null)}
        onDecide={handleDecide}
      />

      {/* Institutional Footer */}
      <Footer />
    </div>
  )
}
