import React, { useState } from 'react'

export default function AgentWorkflow({ onSelectInvoiceForInspection }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'user',
      time: '10:42 AM',
      text: 'Favor procesar pago correspondiente al periodo de cómputo en la nube.',
      file: {
        name: 'Factura_AWS_Cloud_0924.pdf',
        size: '1.4 MB',
        type: 'Factura Electrónica'
      }
    },
    {
      id: 2,
      sender: 'agent',
      time: '10:42 AM',
      type: 'ocr_preview',
      ocrData: {
        vendor: 'Amazon Web Services Inc.',
        taxId: '900.231.884-1',
        amountUsd: '$1,420.00 USD',
        sarlaft: '✅ Sin Coincidencias (Limpio)',
        treasury: 'Saldo Bóveda OK ($48,250 USD)'
      }
    },
    {
      id: 3,
      sender: 'agent',
      time: '10:43 AM',
      type: 'dispatch_decision',
      status: 'AUTO_APPROVED',
      ref: '#BLK-9842',
      text: 'Pago aprobado y programado. Conversión a USD con $0.00 FX Markup y justificación registrada en el Audit Log.'
    }
  ])

  const [inputVal, setInputVal] = useState('')
  const [isSimulating, setIsSimulating] = useState(false)

  const handleSendMessage = (e) => {
    e.preventDefault()
    if (!inputVal.trim()) return

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      time: 'Ahora',
      text: inputVal
    }

    setMessages((prev) => [...prev, userMsg])
    setInputVal('')
    setIsSimulating(true)

    // Simulación de respuesta inmediata del agente
    setTimeout(() => {
      const agentReply = {
        id: Date.now() + 1,
        sender: 'agent',
        time: 'Ahora',
        type: 'text_reply',
        text: 'He recibido tu solicitud. Estoy validando la información contra la matriz de 4 capas y el saldo en tesorería...'
      }
      setMessages((prev) => [...prev, agentReply])
      setIsSimulating(false)
    }, 1000)
  }

  return (
    <section className="w-full py-12 lg:py-16 bg-transparent border-b border-brand-border/60" id="telegram-demo">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Section Header */}
        <div className="max-w-2xl space-y-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-bold text-brand-teal uppercase tracking-wider">
            <span className="material-symbols-outlined text-[15px]">send</span>
            Telegram Live Demo • En Tiempo Real
          </div>
          <h2 className="font-display font-bold text-2xl lg:text-3xl text-brand-navy tracking-tight">
            Interactúa con Blinka PayBot directamente desde mensajería segura
          </h2>
          <p className="text-sm text-brand-muted leading-relaxed">
            Sin portales bancarios lentos ni software ERP engorroso. Envía una factura por chat y el agente lee, valida y decide (pagar, frenar o escalar) respetando tus políticas de gobernanza.
          </p>
        </div>

        {/* 2-Column Desktop Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
          {/* Left Column: Interactive Telegram Chat Mockup (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl border border-brand-border shadow-xl overflow-hidden flex flex-col h-[640px]">
            {/* Telegram Header */}
            <div className="bg-brand-navy text-white px-5 py-3.5 flex items-center justify-between border-b border-slate-700">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-brand-teal flex items-center justify-center font-display font-bold text-white text-base shadow-sm">
                  B
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5">
                    <span className="font-display font-semibold text-sm text-white">Blinka PayBot</span>
                    <span className="material-symbols-outlined text-cyan-300 text-[15px]">verified</span>
                  </div>
                  <span className="text-[11px] text-slate-300 font-mono">en línea • agente de tesorería institucional</span>
                </div>
              </div>

              <div className="flex items-center gap-1 text-slate-300">
                <a
                  href="https://t.me/blinka_paybot"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded hover:bg-white/10 text-xs font-mono text-cyan-300 flex items-center gap-1"
                  title="Abrir en Telegram real"
                >
                  <span>@blinka_paybot</span>
                  <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                </a>
              </div>
            </div>

            {/* Telegram Message Stream */}
            <div className="flex-1 p-4 sm:p-5 bg-slate-50 overflow-y-auto space-y-4 flex flex-col">
              {messages.map((msg) => {
                if (msg.sender === 'user') {
                  return (
                    <div key={msg.id} className="flex flex-col items-end gap-1 ml-auto max-w-sm">
                      <div className="bg-brand-navy text-white p-3.5 rounded-2xl rounded-tr-none flex flex-col gap-2 shadow-sm">
                        {msg.file && (
                          <div className="flex items-center gap-2.5 bg-slate-800 p-2.5 rounded-xl border border-slate-700">
                            <div className="w-9 h-9 rounded-lg bg-red-500/20 text-red-400 flex items-center justify-center border border-red-500/30">
                              <span className="material-symbols-outlined text-[20px]">picture_as_pdf</span>
                            </div>
                            <div className="flex flex-col overflow-hidden">
                              <span className="font-mono text-xs font-semibold text-white truncate">
                                {msg.file.name}
                              </span>
                              <span className="text-[10px] text-slate-300">{msg.file.size} • {msg.file.type}</span>
                            </div>
                          </div>
                        )}
                        <p className="text-xs text-slate-100">{msg.text}</p>
                        <div className="flex justify-end items-center gap-1 text-[10px] text-slate-300">
                          <span>{msg.time}</span>
                          <span className="material-symbols-outlined text-[13px] text-brand-teal">done_all</span>
                        </div>
                      </div>
                    </div>
                  )
                }

                if (msg.type === 'ocr_preview') {
                  return (
                    <div key={msg.id} className="flex flex-col items-start gap-1 mr-auto max-w-md w-full">
                      <div className="bg-white text-brand-navy p-3.5 rounded-2xl rounded-tl-none border border-brand-border shadow-sm flex flex-col gap-2 w-full">
                        <div className="flex items-center justify-between pb-1 border-b border-brand-border/60">
                          <span className="text-[11px] font-bold text-brand-teal flex items-center gap-1">
                            <span className="material-symbols-outlined text-[14px]">document_scanner</span>
                            Extracción OCR Completada
                          </span>
                          <span className="font-mono text-[10px] text-brand-muted">Gemini Flash</span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 p-2.5 rounded-xl bg-slate-50 border border-brand-border/60 font-mono text-xs">
                          <div>
                            <span className="text-[10px] text-brand-muted block font-sans">Proveedor</span>
                            <span className="font-semibold text-brand-navy truncate block">{msg.ocrData.vendor}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-brand-muted block font-sans">Tax ID / RUT</span>
                            <span className="font-semibold text-brand-navy block">{msg.ocrData.taxId}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-brand-muted block font-sans">Monto Total</span>
                            <span className="font-bold text-brand-navy block">{msg.ocrData.amountUsd}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-brand-muted block font-sans">Filtro SARLAFT</span>
                            <span className="text-emerald-700 font-semibold text-[11px] block">{msg.ocrData.sarlaft}</span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between text-[10px] text-brand-muted pt-0.5">
                          <span className="flex items-center gap-1 font-mono">
                            <span className="w-1.5 h-1.5 rounded-full bg-brand-teal"></span>
                            {msg.ocrData.treasury}
                          </span>
                          <span>{msg.time}</span>
                        </div>
                      </div>
                    </div>
                  )
                }

                if (msg.type === 'dispatch_decision') {
                  return (
                    <div key={msg.id} className="flex flex-col items-start gap-1 mr-auto max-w-md w-full">
                      <div className="bg-white text-brand-navy p-3.5 rounded-2xl rounded-tl-none border border-brand-border shadow-sm flex flex-col gap-2.5 w-full">
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 w-fit">
                          <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></span>
                          <span className="font-mono text-xs font-bold">{msg.status} ⚡ {msg.ref}</span>
                        </div>

                        <p className="text-xs text-brand-steel leading-relaxed">{msg.text}</p>

                        <div className="flex items-center gap-2 pt-1 border-t border-brand-border/60">
                          <button
                            onClick={() => onSelectInvoiceForInspection && onSelectInvoiceForInspection({
                              id: 1,
                              invoice_number: 'FE-8921',
                              vendor_name: 'Amazon Web Services Inc.',
                              original_amount: 1420.00,
                              original_currency: 'USD',
                              usd_amount: 1420.00,
                              decision_status: 'AUTO_APPROVED',
                              audit_explanation: 'Monto inferior al umbral autónomo de $2,000 USD. Proveedor verificado en lista blanca con 14 pagos históricos idénticos. Chequeo SARLAFT limpio y fondos disponibles.'
                            })}
                            className="px-3 py-1.5 rounded-lg bg-brand-navy hover:bg-brand-steel text-white text-[11px] font-semibold transition-colors shadow-xs"
                          >
                            Ver Comprobante & Rastro
                          </button>
                          <a
                            href="#reglas-gobernanza"
                            className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-brand-navy text-[11px] font-medium transition-colors border border-brand-border"
                          >
                            Modificar Regla
                          </a>
                        </div>

                        <div className="flex justify-end text-[10px] text-brand-muted">
                          <span>{msg.time}</span>
                        </div>
                      </div>
                    </div>
                  )
                }

                return (
                  <div key={msg.id} className="flex flex-col items-start gap-1 mr-auto max-w-md">
                    <div className="bg-white p-3 rounded-2xl rounded-tl-none border border-brand-border text-xs text-brand-navy shadow-sm">
                      {msg.text}
                    </div>
                  </div>
                )
              })}

              {isSimulating && (
                <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-brand-border text-xs text-brand-muted w-fit animate-pulse">
                  <span className="material-symbols-outlined text-[16px] text-brand-teal animate-spin">sync</span>
                  <span>Blinka PayBot está escribiendo...</span>
                </div>
              )}
            </div>

            {/* Telegram Input Bar */}
            <form onSubmit={handleSendMessage} className="bg-white p-3 border-t border-brand-border flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setInputVal('Subir factura PDF para pago de servicios de telecomunicaciones...')
                }}
                className="p-2 rounded-lg hover:bg-slate-100 text-brand-muted"
                title="Adjuntar factura ejemplo"
              >
                <span className="material-symbols-outlined text-[20px]">attach_file</span>
              </button>

              <input
                type="text"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                placeholder="Escribe al agente o adjunta factura..."
                className="flex-1 bg-slate-50 border border-brand-border px-3.5 py-2 rounded-xl text-xs text-brand-navy outline-none focus:border-brand-teal transition-colors"
              />

              <button
                type="submit"
                className="p-2 rounded-xl bg-brand-teal text-white hover:bg-brand-tealHover transition-all shadow-xs"
                title="Enviar mensaje"
              >
                <span className="material-symbols-outlined text-[18px]">send</span>
              </button>
            </form>
          </div>

          {/* Right Column: "Cómo piensa el Agente" (6 cols) */}
          <div className="lg:col-span-6 flex flex-col gap-4">
            {/* Card 1 */}
            <div className="bg-brand-bg rounded-2xl border border-brand-border p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-white border border-brand-border flex items-center justify-center text-brand-teal shadow-xs">
                  <span className="material-symbols-outlined text-[22px]">receipt_long</span>
                </div>
                <h3 className="font-display font-semibold text-lg text-brand-navy">
                  1. Ingesta Multicanal & OCR Instantáneo
                </h3>
                <p className="text-xs text-brand-muted leading-relaxed">
                  Recibe facturas en PDF o imagen desde Telegram (WhatsApp y correo como canales futuros). El motor de visión (Gemini Flash) extrae proveedor, NIT, monto, moneda, fecha límite y datos bancarios en formato estructurado.
                </p>
              </div>
              <div className="pt-3 border-t border-brand-border/60">
                <span className="inline-flex items-center gap-1.5 font-mono text-[11px] font-semibold text-brand-steel">
                  <span className="material-symbols-outlined text-brand-teal text-[15px]">check_circle</span>
                  PDF, Fotos & Scans
                </span>
              </div>
            </div>

            {/* Card 2 */}
            <div className="bg-brand-bg rounded-2xl border border-brand-border p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-white border border-brand-border flex items-center justify-center text-brand-teal shadow-xs">
                  <span className="material-symbols-outlined text-[22px]">policy</span>
                </div>
                <h3 className="font-display font-semibold text-lg text-brand-navy">
                  2. Matriz de Control Cuádruple
                </h3>
                <p className="text-xs text-brand-muted leading-relaxed">
                  Antes de aprobar cualquier pago, un motor determinista evalúa 4 capas: compliance SARLAFT/OFAC, integridad y duplicados (ventana de 30 días), solvencia y presupuesto, y gobierno con límite de autonomía ($2,000 USD).
                </p>
              </div>
              <div className="pt-3 border-t border-brand-border/60">
                <span className="inline-flex items-center gap-1.5 font-mono text-[11px] font-semibold text-brand-steel">
                  <span className="material-symbols-outlined text-brand-teal text-[15px]">shield</span>
                  Filtro PEP, OFAC & Duplicados
                </span>
              </div>
            </div>

            {/* Card 3 */}
            <div className="bg-brand-bg rounded-2xl border border-brand-border p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-white border border-brand-border flex items-center justify-center text-brand-teal shadow-xs">
                  <span className="material-symbols-outlined text-[22px]">account_balance</span>
                </div>
                <h3 className="font-display font-semibold text-lg text-brand-navy">
                  3. Decisión Explicable & Audit Log
                </h3>
                <p className="text-xs text-brand-muted leading-relaxed">
                  Emite la decisión (aprobar, frenar o escalar a un humano con botones en Telegram), convierte a USD con <strong>$0.00 FX Markup</strong> garantizado por Blinka y registra la justificación en lenguaje natural. No mueve dinero real.
                </p>
              </div>
              <div className="pt-3 border-t border-brand-border/60">
                <span className="inline-flex items-center gap-1.5 font-mono text-[11px] font-semibold text-brand-steel">
                  <span className="material-symbols-outlined text-brand-teal text-[15px]">lock</span>
                  Audit Log persistido en PostgreSQL
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
