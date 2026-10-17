import React, { useState } from 'react'
import { TELEGRAM_BOT_URL } from '../api'

export default function SecurityCompliance({ isModalOpen, onToggleModal }) {
  const [submitted, setSubmitted] = useState(false)
  const [email, setEmail] = useState('')
  const [company, setCompany] = useState('')

  const handleDemoSubmit = (e) => {
    e.preventDefault()
    if (!email) return
    setSubmitted(true)
    setTimeout(() => {
      setSubmitted(false)
      setEmail('')
      setCompany('')
      if (onToggleModal) onToggleModal(false)
    }, 2000)
  }

  return (
    <>
      <section className="w-full py-12 lg:py-16 bg-transparent border-b border-brand-border/60" id="seguridad">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-brand-navy rounded-2xl p-8 lg:p-12 text-white shadow-xl relative overflow-hidden flex flex-col items-center text-center space-y-6">
            {/* Ambient Background Glows */}
            <div className="absolute -bottom-24 -left-24 w-72 h-72 bg-brand-teal/20 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -top-24 -right-24 w-72 h-72 bg-brand-steel/40 rounded-full blur-3xl pointer-events-none" />

            {/* Shield Accent Icon */}
            <div className="w-14 h-14 rounded-2xl bg-brand-steel flex items-center justify-center text-brand-teal shadow-md border border-slate-700">
              <span className="material-symbols-outlined text-[32px]">verified_user</span>
            </div>

            {/* Headline & Copy */}
            <div className="max-w-2xl space-y-2">
              <h2 className="font-display font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
                Comienza a automatizar pagos corporativos de forma segura
              </h2>
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Conecta tu canal de Telegram (WhatsApp y correo próximamente), define tus reglas de gobernanza y obtén decisiones explicables con normalización multidivisa para Latinoamérica.
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center gap-4 pt-2">
              <button
                onClick={() => onToggleModal(true)}
                className="px-6 py-3 rounded-xl bg-brand-teal text-white font-semibold text-sm hover:bg-brand-tealHover transition-all shadow-md active:scale-95"
              >
                Agendar Demo Empresarial
              </button>

              <a
                href={TELEGRAM_BOT_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="px-5 py-3 rounded-xl text-slate-300 hover:text-white font-semibold text-sm transition-colors flex items-center gap-1.5"
              >
                <span>Hablar con el Agente en Telegram</span>
                <span className="material-symbols-outlined text-[16px]">chevron_right</span>
              </a>
            </div>

            {/* Compliance Badges Strip */}
            <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 pt-4 text-xs text-slate-300 border-t border-slate-700/60 w-full max-w-3xl font-mono">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-brand-teal text-[16px]">check</span>
                HTTPS en Railway
              </span>
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-brand-teal text-[16px]">check</span>
                Audit Log Persistido
              </span>
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-brand-teal text-[16px]">check</span>
                Multidivisa LATAM
              </span>
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-brand-teal text-[16px]">check</span>
                Reglas SARLAFT / OFAC
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Modal for Agendar Demo */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-[#04243C]/50 backdrop-blur-sm transition-opacity"
            onClick={() => onToggleModal(false)}
          />

          <div className="relative bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl z-10 border border-brand-border space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-brand-border">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-brand-teal flex items-center justify-center text-white font-bold text-sm">
                  B
                </div>
                <h3 className="font-display font-bold text-base text-brand-navy">Agendar Demostración</h3>
              </div>
              <button
                onClick={() => onToggleModal(false)}
                className="p-1 rounded-lg text-brand-muted hover:bg-slate-100"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            {submitted ? (
              <div className="py-8 text-center space-y-2">
                <span className="material-symbols-outlined text-emerald-500 text-[48px]">check_circle</span>
                <h4 className="font-display font-bold text-base text-brand-navy">¡Solicitud Recibida!</h4>
                <p className="text-xs text-brand-muted">
                  Un especialista de Blinka PayAgent se pondrá en contacto en menos de 2 horas.
                </p>
              </div>
            ) : (
              <form onSubmit={handleDemoSubmit} className="space-y-3">
                <p className="text-xs text-brand-muted">
                  Descubre cómo implementar agentes de pago autónomos en tu empresa con gobernanza financiera.
                </p>

                <div>
                  <label className="block text-[11px] font-semibold text-brand-navy uppercase mb-1">
                    Correo Corporativo
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="cfo@tuempresa.com"
                    className="w-full px-3.5 py-2 bg-slate-50 border border-brand-border rounded-xl text-xs text-brand-navy outline-none focus:border-brand-teal"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-brand-navy uppercase mb-1">
                    Nombre de la Empresa
                  </label>
                  <input
                    type="text"
                    required
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="Empresa LATAM S.A.S"
                    className="w-full px-3.5 py-2 bg-slate-50 border border-brand-border rounded-xl text-xs text-brand-navy outline-none focus:border-brand-teal"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2.5 rounded-xl bg-brand-navy hover:bg-brand-steel text-white text-xs font-semibold transition-all shadow-sm active:scale-95"
                >
                  Confirmar Agendamiento
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  )
}
