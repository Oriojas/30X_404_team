import React, { useCallback, useEffect, useLayoutEffect, useMemo, useState } from 'react'
// Mismo mapa de estados y badge que el dashboard (src/status.js)
import StatusBadge from './StatusBadge'

/**
 * Presentación comercial (Slide Deck) de Blinka PayAgent.
 * Ruta: #/pitch  |  #/pitch/3 (slide específica)
 * Atajos: ← → Espacio · Inicio/Fin · F pantalla completa · N notas · H ocultar controles
 *
 * El contenido sigue docs/pitch_presentacion/presentacion_y_guion.md (Parte 1)
 * y el sistema de diseño de docs/diseno/DESIGN.md.
 */

const STAGE_W = 1280
const STAGE_H = 720

/* ------------------------------------------------------------------ */
/* Primitivas de diseño (DESIGN.md: bordes 1px, radios 4–6px, pills    */
/* solo para badges de estado)                                         */
/* ------------------------------------------------------------------ */

function Icon({ name, className = '' }) {
  return <span className={`material-symbols-outlined ${className}`}>{name}</span>
}

function Eyebrow({ children, dark }) {
  return (
    <span
      className={`font-mono text-[13px] font-semibold uppercase tracking-[0.18em] ${
        dark ? 'text-cyan-300' : 'text-brand-teal'
      }`}
    >
      {children}
    </span>
  )
}

function SlideFrame({ dark, index, total, children }) {
  return (
    <div
      className={`relative w-full h-full overflow-hidden ${
        dark ? 'bg-brand-navy text-white' : 'bg-brand-bg text-brand-navy'
      }`}
    >
      {/* Curvas de nivel sutiles (identidad Blinka) */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        viewBox="0 0 1280 720"
        fill="none"
        aria-hidden="true"
      >
        {[0, 1, 2, 3, 4, 5, 6].map((i) => (
          <ellipse
            key={i}
            cx="1120"
            cy="640"
            rx={140 + i * 70}
            ry={90 + i * 48}
            stroke={dark ? '#2B9CAE' : '#1D3557'}
            strokeOpacity={dark ? 0.16 : 0.05}
            strokeWidth="1"
          />
        ))}
      </svg>

      {/* Cabecera */}
      <div className="absolute top-0 left-0 right-0 h-16 px-16 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div
            className={`w-7 h-7 rounded flex items-center justify-center font-display font-bold text-sm ${
              dark ? 'bg-brand-teal text-white' : 'bg-brand-navy text-white'
            }`}
          >
            B
          </div>
          <span className="font-display font-bold text-base tracking-tight">
            Blinka <span className="text-brand-teal">PayAgent</span>
          </span>
        </div>
        <span className={`font-mono text-xs tracking-widest ${dark ? 'text-slate-300' : 'text-brand-muted'}`}>
          HACKATHON 30X · EQUIPO 404 · {String(index + 1).padStart(2, '0')}/{String(total).padStart(2, '0')}
        </span>
      </div>

      <div className="absolute inset-0 pt-16 px-16 pb-14 z-10 flex flex-col">{children}</div>
    </div>
  )
}

function SlideTitle({ eyebrow, title, dark }) {
  return (
    <div className="space-y-3 pt-6">
      <Eyebrow dark={dark}>{eyebrow}</Eyebrow>
      <h2 className="font-display font-bold text-[40px] leading-[1.15] tracking-tight max-w-[1000px]">{title}</h2>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Slides                                                              */
/* ------------------------------------------------------------------ */

function SlideCover() {
  return (
    <div className="flex-1 grid grid-cols-12 gap-12 items-center">
      <div className="col-span-7 space-y-7">
        <Eyebrow dark>Hackathon 30X · Reto Blinka</Eyebrow>
        <h1 className="font-display font-extrabold text-[72px] leading-[1.02] tracking-tight">
          Blinka <span className="text-brand-teal">PayAgent</span>
        </h1>
        <p className="font-display font-semibold text-[28px] leading-[1.3] text-slate-100 max-w-[640px]">
          Agentes IA de decisión de pagos con gobernanza financiera.
        </p>
        <p className="text-[18px] leading-relaxed text-slate-300 max-w-[600px]">
          Cero pagos indebidos, conversión de divisas sin sobrecosto y trazabilidad total.
        </p>
        <div className="inline-flex items-center gap-3 rounded-md border border-white/15 bg-white/5 px-5 py-3 text-[16px] text-slate-100">
          <Icon name="verified_user" className="text-cyan-300 text-[22px]" />
          Un proceso autónomo, seguro y 100% auditable.
        </div>
      </div>

      {/* Mockup: Telegram → decisión */}
      <div className="col-span-5">
        <div className="rounded-md border border-white/15 bg-white/5 p-6 space-y-4">
          <div className="flex items-center gap-2 text-[12px] font-mono text-slate-300">
            <Icon name="send" className="text-[16px] text-cyan-300" />
            Telegram · Blinka PayBot
          </div>

          <div className="ml-auto max-w-[300px] rounded-md rounded-tr-none bg-brand-steel p-3.5 space-y-2">
            <div className="flex items-center gap-3 rounded border border-white/10 bg-black/20 p-2.5">
              <Icon name="picture_as_pdf" className="text-red-300 text-[24px]" />
              <div className="font-mono text-[12px] leading-tight">
                Factura_AWS_Cloud.pdf
                <div className="text-slate-300 text-[11px]">1.4 MB</div>
              </div>
            </div>
          </div>

          <div className="rounded-md rounded-tl-none border border-white/10 bg-white p-4 text-brand-navy space-y-3">
            <div className="flex items-center justify-between font-mono text-[11px] text-brand-muted">
              <span>Extracción OCR · Gemini Flash</span>
              <span>Capas 1–4 ✓</span>
            </div>
            <div className="grid grid-cols-2 gap-2 font-mono text-[12px]">
              <div>
                <div className="font-sans text-[10px] text-brand-muted">Proveedor</div>
                AWS Cloud Services
              </div>
              <div>
                <div className="font-sans text-[10px] text-brand-muted">Monto convertido</div>
                $285.71 USD
              </div>
            </div>
            <StatusBadge status="AUTO_APPROVED" size="slide" />
          </div>
        </div>
      </div>
    </div>
  )
}

function SlideProblem() {
  const pains = [
    {
      icon: 'hourglass_top',
      title: 'Ineficiencia operativa',
      text: 'Cientos de horas perdidas revisando facturas por correo, WhatsApp o PDF a mano.'
    },
    {
      icon: 'currency_exchange',
      title: 'Fricción multidivisa',
      text: 'Facturas en COP, MXN, EUR, BRL o ARS pagadas desde tesorerías en USD, con altas comisiones de cambio (FX markups).'
    },
    {
      icon: 'gpp_maybe',
      title: 'Riesgo de pagos indebidos',
      text: 'Cobros duplicados (<30 días) o proveedores en listas restrictivas (SARLAFT / OFAC / ONU) que pasan inadvertidos.'
    }
  ]
  return (
    <>
      <SlideTitle eyebrow="El problema" title="El cuello de botella de cuentas por pagar en empresas globales." />
      <div className="flex-1 grid grid-cols-3 gap-6 items-center">
        {pains.map((p, i) => (
          <div key={p.title} className="rounded-md border border-brand-border bg-white p-7 h-[300px] flex flex-col gap-4 shadow-[0_1px_2px_0_rgba(4,36,60,0.04)]">
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded bg-slate-100 border border-brand-border flex items-center justify-center text-brand-teal">
                <Icon name={p.icon} className="text-[28px]" />
              </div>
              <span className="font-mono text-[13px] text-brand-muted">0{i + 1}</span>
            </div>
            <h3 className="font-display font-semibold text-[22px] leading-tight">{p.title}</h3>
            <p className="text-[16px] leading-relaxed text-brand-muted">{p.text}</p>
          </div>
        ))}
      </div>
      <div className="rounded-md border border-brand-border bg-white px-6 py-4 text-[17px] text-brand-steel flex items-center gap-3">
        <Icon name="timer" className="text-brand-teal" />
        Las validaciones manuales repetitivas consumen la mayor parte del tiempo de los equipos de finanzas.
      </div>
    </>
  )
}

function SlideSolution() {
  const decisions = [
    { status: 'AUTO_APPROVED', verb: 'Pagar', text: 'Proveedor verificado, dentro del umbral y con saldo.' },
    { status: 'REJECTED', verb: 'Frenar', text: 'Duplicado o coincidencia en lista restrictiva.' },
    { status: 'SCALED_TO_HUMAN', verb: 'Escalar', text: 'Supera el umbral, proveedor nuevo o saldo insuficiente. Decide una persona en el dashboard.' }
  ]
  const pillars = [
    { icon: 'bolt', title: 'Autonomía', text: 'Facturas de proveedores con historial y bajo $2,000 USD se aprueban solas.' },
    { icon: 'shield', title: 'Seguridad', text: 'Rechazo inmediato de duplicados y listas restrictivas; ante la duda, escala.' },
    { icon: 'visibility', title: 'Explicabilidad', text: 'Cada decisión con justificación en lenguaje natural y regla disparada.' }
  ]
  return (
    <>
      <SlideTitle eyebrow="La solución" title="Gobernanza financiera autónomamente ejecutada." />
      <p className="text-[18px] text-brand-muted max-w-[900px] mt-3">
        Un agente conectado a Telegram lee facturas multimodales, aplica las reglas de negocio de Blinka y emite la
        decisión idónea.
      </p>

      <div className="grid grid-cols-3 gap-6 mt-10">
        {decisions.map((d) => (
          <div key={d.verb} className="rounded-md border border-brand-border bg-white p-6 space-y-3 shadow-[0_1px_2px_0_rgba(4,36,60,0.04)]">
            <StatusBadge status={d.status} size="slideLg" />
            <div className="font-display font-bold text-[34px] leading-none">{d.verb}</div>
            <p className="text-[15px] leading-relaxed text-brand-muted">{d.text}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6 mt-10 flex-1 items-start">
        {pillars.map((p) => (
          <div key={p.title} className="flex gap-4">
            <div className="w-11 h-11 shrink-0 rounded bg-brand-navy text-brand-teal flex items-center justify-center">
              <Icon name={p.icon} className="text-[24px]" />
            </div>
            <div>
              <div className="font-display font-semibold text-[19px]">{p.title}</div>
              <p className="text-[15px] leading-relaxed text-brand-muted mt-1">{p.text}</p>
            </div>
          </div>
        ))}
      </div>

      <p className="font-mono text-[12px] text-brand-muted">
        * El agente decide y registra; no ejecuta pagos reales ni mueve dinero.
      </p>
    </>
  )
}

function SlideArchitecture() {
  const coreSteps = [
    { n: '1', title: 'Gemini Flash', sub: 'OCR multimodal + extracción JSON' },
    { n: '2', title: 'FX Engine', sub: 'Normaliza a USD · $0.00 markup' },
    { n: '3', title: 'Reglas Blinka', sub: '4 capas deterministas · sin LLM' },
    { n: '4', title: 'Audit Logger', sub: 'Explicación en lenguaje natural' }
  ]
  const layers = [
    { n: 'Capa 1', title: 'Compliance & SARLAFT', text: 'OFAC / ONU / GAFI, cuentas, PEP y NIT' },
    { n: 'Capa 2', title: 'Integridad', text: 'Duplicados (30 días) y confianza OCR ≥ 85%' },
    { n: 'Capa 3', title: 'Solvencia', text: 'Saldo en Blinka y presupuesto del período' },
    { n: 'Capa 4', title: 'Gobierno HITL', text: 'Umbral $2,000 USD y proveedor nuevo' }
  ]
  return (
    <>
      <SlideTitle eyebrow="Arquitectura" title="Hexagonal, desacoplada y determinista." />

      <div className="grid grid-cols-12 gap-4 mt-6 items-stretch">
        {/* Entrada */}
        <div className="col-span-2 rounded-md border border-brand-border bg-white p-4 space-y-3">
          <div className="font-mono text-[11px] uppercase tracking-widest text-brand-muted">Entrada</div>
          <div className="rounded border border-brand-teal bg-cyan-50 px-3 py-2 text-[14px] font-semibold flex items-center gap-2">
            <Icon name="send" className="text-[18px] text-brand-teal" /> Telegram
          </div>
          <div className="rounded border border-dashed border-slate-300 px-3 py-2 text-[13px] text-brand-muted">
            WhatsApp · Correo
            <div className="font-mono text-[10px]">canales futuros</div>
          </div>
        </div>

        <div className="col-span-1 flex items-center justify-center text-brand-teal">
          <Icon name="arrow_forward" className="text-[28px]" />
        </div>

        {/* Core */}
        <div className="col-span-6 rounded-md border border-brand-navy bg-white p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="font-mono text-[11px] uppercase tracking-widest text-brand-muted">Core del agente · FastAPI</div>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {coreSteps.map((s) => (
              <div key={s.n} className="rounded border border-brand-border bg-brand-bg p-3 min-h-[104px]">
                <div className="font-mono text-[11px] text-brand-teal font-bold">{s.n}</div>
                <div className="font-display font-semibold text-[15px] leading-tight mt-1">{s.title}</div>
                <div className="text-[12px] text-brand-muted leading-snug mt-1">{s.sub}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-1 flex items-center justify-center text-brand-teal">
          <Icon name="arrow_forward" className="text-[28px]" />
        </div>

        {/* Salida */}
        <div className="col-span-2 rounded-md border border-brand-border bg-white p-4 space-y-3">
          <div className="font-mono text-[11px] uppercase tracking-widest text-brand-muted">Persistencia / UI</div>
          <div className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-[14px] font-semibold flex items-center gap-2">
            <Icon name="database" className="text-[18px] text-brand-steel" /> PostgreSQL
          </div>
          <div className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-[14px] font-semibold flex items-center gap-2">
            <Icon name="dashboard" className="text-[18px] text-brand-steel" /> Dashboard React
          </div>
        </div>
      </div>

      <div className="mt-7 flex-1">
        <div className="font-mono text-[11px] uppercase tracking-widest text-brand-muted mb-3">
          Pipeline de 4 capas · se detiene ante la primera falla crítica
        </div>
        <div className="grid grid-cols-4 gap-4">
          {layers.map((l) => (
            <div key={l.n} className="rounded-md border border-brand-border bg-white p-4 border-t-2 border-t-brand-teal">
              <div className="font-mono text-[11px] font-bold text-brand-teal">{l.n}</div>
              <div className="font-display font-semibold text-[17px] mt-1">{l.title}</div>
              <p className="text-[13px] text-brand-muted leading-snug mt-1.5">{l.text}</p>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function SlideAudit() {
  const rows = [
    {
      vendor: 'AWS Cloud Services',
      original: '1,200,000 COP',
      usd: '$285.71',
      status: 'AUTO_APPROVED',
      rule: '—',
      why: 'Proveedor verificado, saldo suficiente y dentro del límite autónomo.'
    },
    {
      vendor: 'AWS Cloud Services',
      original: '1,200,000 COP',
      usd: '$285.71',
      status: 'REJECTED',
      rule: 'INTEG-01',
      why: 'Cobro duplicado detectado dentro de la ventana de 30 días.'
    },
    {
      vendor: 'Oracle Enterprise',
      original: '3,200 EUR',
      usd: '$3,478.26',
      status: 'SCALED_TO_HUMAN',
      rule: 'HITL-01',
      why: 'Excede el límite autónomo de $2,000 USD. Requiere aprobación humana.'
    },
    {
      vendor: 'Logística Express MX',
      original: '117,000 MXN',
      usd: '$6,000.00',
      status: 'HUMAN_APPROVED',
      rule: 'HITL-01',
      why: 'Escalada por el umbral; aprobada por el CFO en el dashboard, con nota en el Audit Log.'
    }
  ]
  return (
    <>
      <SlideTitle eyebrow="Demo · Audit Log" title="Transparencia y control en tiempo real." />

      <div className="mt-6 rounded-md border border-brand-border bg-white overflow-hidden shadow-[0_1px_2px_0_rgba(4,36,60,0.04)]">
        <div className="grid grid-cols-[1.4fr_1.1fr_0.8fr_1.5fr_0.8fr_2.6fr] gap-4 px-5 py-3 bg-brand-bg border-b border-brand-border font-mono text-[11px] uppercase tracking-wider text-brand-muted">
          <span>Proveedor</span>
          <span>Monto original</span>
          <span>USD</span>
          <span>Estado</span>
          <span>Regla</span>
          <span>Explicación</span>
        </div>
        {rows.map((r, i) => (
          <div
            key={i}
            className="grid grid-cols-[1.4fr_1.1fr_0.8fr_1.5fr_0.8fr_2.6fr] gap-4 px-5 py-6 items-center border-b border-slate-100 last:border-b-0 text-[15px]"
          >
            <span className="font-semibold">{r.vendor}</span>
            <span className="font-mono tabular-data">{r.original}</span>
            <span className="font-mono tabular-data font-semibold">{r.usd}</span>
            <span>
              <StatusBadge status={r.status} size="slide" />
            </span>
            <span className="font-mono text-[13px] text-brand-steel">{r.rule}</span>
            <span className="text-[13px] leading-snug text-brand-muted">{r.why}</span>
          </div>
        ))}
      </div>

      <div className="flex-1 flex items-end justify-between gap-6">
        <div className="flex flex-wrap gap-3 text-[14px] text-brand-steel">
          {['Umbral configurable', 'Detalle por factura', 'Regla disparada', 'Aprobación humana en el dashboard'].map((t) => (
            <span key={t} className="inline-flex items-center gap-2 rounded border border-brand-border bg-white px-3 py-1.5">
              <Icon name="check_circle" className="text-brand-teal text-[18px]" />
              {t}
            </span>
          ))}
        </div>
        <a
          href="#auditoria"
          className="inline-flex items-center gap-2 rounded bg-brand-navy hover:bg-brand-steel text-white px-5 py-3 font-semibold text-[15px] transition-colors"
        >
          Abrir dashboard en vivo
          <Icon name="arrow_forward" className="text-[18px]" />
        </a>
      </div>
    </>
  )
}

function SlideImpact() {
  const metrics = [
    { big: '~90%', label: 'menos carga manual', note: 'Estimación de diseño' },
    { big: '$0.00', label: 'markup cambiario', note: 'Garantía de cuentas Blinka' },
    { big: '0', label: 'pagos fuera de reglas', note: 'Por diseño: ante la duda, escala' },
    { big: '1', label: 'llamada a Gemini por factura', note: 'Reglas sin costo de inferencia' }
  ]
  return (
    <>
      <SlideTitle dark eyebrow="Impacto y viabilidad" title="Resultados medibles para Blinka y sus clientes." />

      <div className="grid grid-cols-4 gap-5 mt-8">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-md border border-white/15 bg-white/5 p-6 space-y-2">
            <div className="font-display font-extrabold text-[48px] leading-none text-cyan-300">{m.big}</div>
            <div className="font-display font-semibold text-[18px] leading-snug">{m.label}</div>
            <div className="font-mono text-[11px] text-slate-300">{m.note}</div>
          </div>
        ))}
      </div>

      <div className="flex-1 grid grid-cols-12 gap-6 items-end">
        <div className="col-span-7 space-y-3">
          <div className="font-mono text-[12px] uppercase tracking-widest text-slate-300">Siguiente paso</div>
          <p className="text-[19px] leading-relaxed text-slate-100">
            Desplegado en Railway, código abierto en GitHub y listo para escalar a WhatsApp y correo corporativo sin
            tocar la lógica de negocio.
          </p>
        </div>
        <div className="col-span-5 rounded-md border border-white/15 bg-white/5 p-5 space-y-3 font-mono text-[14px]">
          <div className="flex items-center gap-3">
            <Icon name="language" className="text-cyan-300 text-[20px]" />
            30x404team-production.up.railway.app
          </div>
          <div className="flex items-center gap-3">
            <Icon name="code" className="text-cyan-300 text-[20px]" />
            github.com/Oriojas/30X_404_team
          </div>
        </div>
      </div>
    </>
  )
}

const SLIDES = [
  {
    id: 'portada',
    dark: true,
    notes: '0:00 · Gancho. Presentar Blinka PayAgent: recibe facturas por Telegram, las lee con Gemini, convierte divisas sin sobrecosto y decide qué pagar, frenar o escalar.',
    Component: SlideCover
  },
  {
    id: 'problema',
    notes: '0:00–0:15 · Cientos de horas en facturas manuales, monedas locales y riesgo de pagos duplicados o a listas restrictivas.',
    Component: SlideProblem
  },
  {
    id: 'solucion',
    notes: '0:15–0:35 · Pagar, Frenar o Escalar. Aclarar que el agente decide y registra; no mueve dinero real.',
    Component: SlideSolution
  },
  {
    id: 'arquitectura',
    notes: '2:20–2:45 · Gemini solo lee la factura; las decisiones las toma un motor determinista de 4 capas. Telegram es un adaptador: se pueden sumar correo o WhatsApp sin tocar el Core.',
    Component: SlideArchitecture
  },
  {
    id: 'demo',
    notes: '0:35–2:20 · Demo: caso 1 aprobado, caso 2 duplicado, caso 3 escalado. Luego abrir el dashboard en vivo, mostrar explicación + regla disparada y aprobar el escalamiento desde el Drawer (queda HUMAN_APPROVED con quién, cuándo y nota; la autonomía no cuenta decisiones humanas).',
    Component: SlideAudit
  },
  {
    id: 'impacto',
    dark: true,
    notes: '2:45–3:00 · Cierre: ~90% menos carga manual (estimado), $0.00 FX, cero pagos fuera de reglas por diseño. URL y repositorio abierto.',
    Component: SlideImpact
  }
]

/* ------------------------------------------------------------------ */
/* Contenedor del deck                                                 */
/* ------------------------------------------------------------------ */

function parseSlideFromHash() {
  const match = window.location.hash.match(/^#\/pitch\/(\d+)/)
  const n = match ? parseInt(match[1], 10) : 1
  return Math.min(Math.max(n, 1), SLIDES.length) - 1
}

export default function PitchDeck() {
  const [index, setIndex] = useState(parseSlideFromHash)
  const [viewport, setViewport] = useState({ w: window.innerWidth, h: window.innerHeight })
  const [showNotes, setShowNotes] = useState(false)
  const [hideControls, setHideControls] = useState(false)

  const total = SLIDES.length

  const go = useCallback(
    (next) => {
      setIndex((prev) => {
        const target = typeof next === 'function' ? next(prev) : next
        return Math.min(Math.max(target, 0), total - 1)
      })
    },
    [total]
  )

  // Escala el escenario 16:9 al viewport (ideal para grabar el video)
  useLayoutEffect(() => {
    const fit = () => setViewport({ w: window.innerWidth, h: window.innerHeight })
    fit()
    window.addEventListener('resize', fit)
    return () => window.removeEventListener('resize', fit)
  }, [])

  const scale = Math.min(viewport.w / STAGE_W, viewport.h / STAGE_H)

  // Sincroniza la slide con la URL (#/pitch/N) sin generar historial
  useEffect(() => {
    window.history.replaceState(null, '', `#/pitch/${index + 1}`)
  }, [index])

  // Atajos de teclado
  useEffect(() => {
    const onKey = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return
      switch (e.key) {
        case 'ArrowRight':
        case 'PageDown':
        case ' ':
          e.preventDefault()
          go((i) => i + 1)
          break
        case 'ArrowLeft':
        case 'PageUp':
          e.preventDefault()
          go((i) => i - 1)
          break
        case 'Home':
          go(0)
          break
        case 'End':
          go(total - 1)
          break
        case 'f':
        case 'F':
          if (document.fullscreenElement) document.exitFullscreen()
          else document.documentElement.requestFullscreen?.()
          break
        case 'p':
        case 'P':
          window.print()
          break
        case 'n':
        case 'N':
          setShowNotes((v) => !v)
          break
        case 'h':
        case 'H':
          setHideControls((v) => !v)
          break
        default:
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go, total])

  const slide = SLIDES[index]
  const Current = slide.Component

  const stageStyle = useMemo(
    () => ({
      width: STAGE_W,
      height: STAGE_H,
      transform: `scale(${scale})`,
      transformOrigin: 'top left',
      left: (viewport.w - STAGE_W * scale) / 2,
      top: (viewport.h - STAGE_H * scale) / 2
    }),
    [scale, viewport]
  )

  return (
    <>
      {/* Vista Interactiva (en pantalla, oculta al imprimir) */}
      <div className="fixed inset-0 bg-[#0B1C30] overflow-hidden select-none print:hidden" role="region" aria-label="Presentación Blinka PayAgent">
        <div className="absolute shadow-2xl" style={stageStyle}>
          <div key={slide.id} className="pitch-slide-enter w-full h-full">
            <SlideFrame dark={slide.dark} index={index} total={total}>
              <Current />
            </SlideFrame>
          </div>
        </div>

        {/* Barra de progreso */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-white/10">
          <div
            className="h-full bg-brand-teal transition-all duration-300"
            style={{ width: `${((index + 1) / total) * 100}%` }}
          />
        </div>

        {/* Notas del presentador (tecla N) */}
        {showNotes && (
          <div className="absolute left-1/2 -translate-x-1/2 bottom-16 max-w-3xl w-[90%] rounded-md border border-white/15 bg-black/80 text-slate-100 px-5 py-3 text-sm leading-relaxed">
            <span className="font-mono text-[11px] uppercase tracking-widest text-cyan-300 mr-2">Notas</span>
            {slide.notes}
          </div>
        )}

        {/* Controles (tecla H para ocultar) */}
        {!hideControls && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-3 rounded-full border border-white/15 bg-black/50 backdrop-blur px-3.5 py-1.5 opacity-60 hover:opacity-100 transition-opacity">
            <button
              id="pitch-prev"
              onClick={() => go((i) => i - 1)}
              disabled={index === 0}
              className="p-1 text-white disabled:opacity-30 hover:text-cyan-300 transition-colors"
              aria-label="Slide anterior"
            >
              <Icon name="chevron_left" className="text-[22px]" />
            </button>
            <div className="flex items-center gap-1.5">
              {SLIDES.map((s, i) => (
                <button
                  key={s.id}
                  id={`pitch-dot-${s.id}`}
                  onClick={() => go(i)}
                  aria-label={`Ir a la slide ${i + 1}`}
                  className={`h-2 rounded-full transition-all ${
                    i === index ? 'w-6 bg-brand-teal' : 'w-2 bg-white/40 hover:bg-white/70'
                  }`}
                />
              ))}
            </div>
            <button
              id="pitch-next"
              onClick={() => go((i) => i + 1)}
              disabled={index === total - 1}
              className="p-1 text-white disabled:opacity-30 hover:text-cyan-300 transition-colors"
              aria-label="Slide siguiente"
            >
              <Icon name="chevron_right" className="text-[22px]" />
            </button>
            <span className="w-px h-4 bg-white/20" />
            <button
              id="pitch-download-pdf"
              onClick={() => window.print()}
              className="p-1 text-white hover:text-cyan-300 transition-colors flex items-center gap-1"
              aria-label="Descargar presentación en PDF"
              title="Descargar presentación en PDF (P)"
            >
              <Icon name="picture_as_pdf" className="text-[19px]" />
            </button>
            <button
              id="pitch-fullscreen"
              onClick={() => {
                if (document.fullscreenElement) document.exitFullscreen()
                else document.documentElement.requestFullscreen?.()
              }}
              className="p-1 text-white hover:text-cyan-300 transition-colors"
              aria-label="Pantalla completa"
              title="Pantalla completa (F)"
            >
              <Icon name="fullscreen" className="text-[20px]" />
            </button>
            <a href="#" className="p-1 text-white hover:text-red-400 transition-colors" aria-label="Volver a la landing" title="Volver a la landing">
              <Icon name="close" className="text-[20px]" />
            </a>
          </div>
        )}
      </div>

      {/* Contenedor Exclusivo de Impresión / Guardar como PDF (todas las 6 slides) */}
      <div className="hidden print:block print-deck">
        {SLIDES.map((s, i) => {
          const SlideComp = s.Component
          return (
            <div key={`print-${s.id}`} className="print-slide-page">
              <SlideFrame dark={s.dark} index={i} total={total}>
                <SlideComp />
              </SlideFrame>
            </div>
          )
        })}
      </div>
    </>
  )
}

