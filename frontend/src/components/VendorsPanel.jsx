import React, { useState } from 'react'
import Notice from './Notice'
import { formatUsd, parseApiDate } from '../api'

function FieldError({ message }) {
  if (!message) return null
  return <p className="text-[11px] text-red-600 font-sans">{message}</p>
}

const EMPTY_FORM = { tax_id: '', legal_name: '', bank_account: '', contract_amount_usd: '' }
const FORM_FIELDS = ['tax_id', 'legal_name', 'bank_account', 'contract_amount_usd']

function formatChange(vendor) {
  if (!vendor.updated_by) return '—'
  const date = parseApiDate(vendor.updated_at)
  const when = !date || Number.isNaN(date.getTime()) ? '' : ` · ${date.toLocaleString()}`
  return `${vendor.updated_by}${when}`
}

function Field({ label, name, value, onChange, error, disabled, placeholder, type = 'text', hint }) {
  return (
    <label className="flex flex-col gap-1 text-xs">
      <span className="text-brand-muted font-medium">{label}</span>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        disabled={disabled}
        placeholder={placeholder}
        min={type === 'number' ? '0' : undefined}
        className={`bg-white border rounded-lg px-3 py-2 text-xs text-brand-navy font-mono disabled:bg-slate-100 disabled:text-brand-muted ${error ? 'border-red-400' : 'border-brand-border'}`}
      />
      {hint && !error && <span className="text-[10px] text-brand-muted">{hint}</span>}
      <FieldError message={error} />
    </label>
  )
}

// Lista permitida de beneficiarios (F7.3 a F7.5): HITL-02 escala lo que no está aquí o está inactivo.
// El NIT no se edita tras el alta (es la llave de COMP-04) y la condición PEP es de solo lectura.
export default function VendorsPanel({ vendors, loading, error, readOnly = false, onCreate, onUpdate }) {
  // null = formulario cerrado; { id: null } = alta; { id, ... } = edición
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [togglingId, setTogglingId] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [listError, setListError] = useState(null)
  const [notice, setNotice] = useState(null)

  const isCreate = editing && editing.id == null

  const openForm = (vendor) => {
    setEditing(vendor || { id: null })
    setForm(vendor ? {
      tax_id: vendor.tax_id,
      legal_name: vendor.legal_name,
      bank_account: vendor.bank_account || '',
      contract_amount_usd: vendor.contract_amount_usd ?? ''
    } : EMPTY_FORM)
    setFieldErrors({})
    setFormError(null)
    setNotice(null)
  }

  const closeForm = () => {
    setEditing(null)
    setFieldErrors({})
    setFormError(null)
  }

  const handleChange = (e) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))

  const showErrors = (err) => {
    const byField = err.fieldErrors || {}
    setFieldErrors(byField)
    const allShownByField = Object.keys(byField).length > 0 && Object.keys(byField).every((f) => FORM_FIELDS.includes(f))
    if (!allShownByField) setFormError(err.message || 'No se pudo guardar el beneficiario.')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (readOnly || saving) return
    // Tarifa vacía = sin tarifa acordada (null), no 0
    const contract = form.contract_amount_usd === '' ? null : Number(form.contract_amount_usd)
    const payload = { legal_name: form.legal_name.trim(), bank_account: form.bank_account.trim(), contract_amount_usd: contract }

    setSaving(true)
    setFieldErrors({})
    setFormError(null)
    try {
      if (isCreate) {
        const created = await onCreate({ ...payload, tax_id: form.tax_id.trim() })
        setNotice(`${created.legal_name} quedó en la lista permitida: sus próximas facturas ya no escalan por HITL-02.`)
      } else {
        const updated = await onUpdate(editing.id, payload)
        setNotice(`Cambios guardados para ${updated.legal_name}.`)
      }
      closeForm()
    } catch (err) {
      showErrors(err)
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (vendor) => {
    if (readOnly || togglingId) return
    setTogglingId(vendor.id)
    setListError(null)
    setNotice(null)
    try {
      const updated = await onUpdate(vendor.id, { active: !vendor.active })
      setNotice(updated.active
        ? `${updated.legal_name} se reactivó en la lista permitida.`
        : `${updated.legal_name} se dio de baja: sus facturas escalan por HITL-02 y conserva su registro.`)
    } catch (err) {
      setListError(err.message || 'No se pudo cambiar el estado del beneficiario.')
    } finally {
      setTogglingId(null)
    }
  }

  const activeCount = vendors.filter((v) => v.active).length

  return (
    <section className="w-full py-12 lg:py-16 bg-transparent border-b border-brand-border/60" id="beneficiarios">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="max-w-2xl space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-brand-teal uppercase tracking-wider">
              <span className="material-symbols-outlined text-[15px]">verified_user</span>
              Lista Permitida
            </div>
            <h2 className="font-display font-bold text-2xl lg:text-3xl text-brand-navy tracking-tight">
              Beneficiarios Permitidos
            </h2>
            <p className="text-sm text-brand-muted leading-relaxed">
              El agente solo aprueba por su cuenta pagos a proveedores de esta lista, a su cuenta autorizada y dentro de su tarifa acordada. Los demás escalan a un aprobador (HITL-02).
            </p>
          </div>

          <button
            onClick={() => openForm(null)}
            disabled={readOnly || isCreate}
            className="self-start md:self-auto inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-navy hover:bg-brand-steel text-white text-xs font-semibold transition-all shadow-sm active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
          >
            <span className="material-symbols-outlined text-[16px] text-brand-teal">person_add</span>
            <span>Agregar beneficiario</span>
          </button>
        </div>

        {readOnly && (
          <Notice size="lg">Modo demostración: dar de alta o editar beneficiarios se habilita cuando la API responde.</Notice>
        )}
        {error && !readOnly && <Notice tone="error" size="lg">{error}</Notice>}
        {listError && <Notice tone="error" size="lg">{listError}</Notice>}
        {notice && <Notice tone="success" size="lg">{notice}</Notice>}

        {editing && (
          <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-brand-border p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-display font-semibold text-base text-brand-navy">
                {isCreate ? 'Nuevo beneficiario' : `Editar ${editing.legal_name}`}
              </h3>
              {!isCreate && editing.is_pep && (
                <span className="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-[11px] font-semibold">PEP · solo lectura</span>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field
                label="NIT / identificación fiscal" name="tax_id" value={form.tax_id} onChange={handleChange}
                error={fieldErrors.tax_id} disabled={!isCreate} placeholder="900.584.112-4"
                hint={isCreate ? 'No se puede cambiar después del alta.' : 'Fijo: es la llave con que se compara la factura.'}
              />
              <Field label="Razón social" name="legal_name" value={form.legal_name} onChange={handleChange}
                error={fieldErrors.legal_name} placeholder="DevStudio LatAm S.A.S." />
              <Field label="Cuenta bancaria autorizada" name="bank_account" value={form.bank_account} onChange={handleChange}
                error={fieldErrors.bank_account} placeholder="CO-BANCOLOMBIA-11122233344"
                hint="Una factura con otra cuenta escala por COMP-02." />
              <Field label="Tarifa acordada (USD, opcional)" name="contract_amount_usd" type="number"
                value={form.contract_amount_usd} onChange={handleChange} error={fieldErrors.contract_amount_usd}
                placeholder="1500" hint="Cobrar más que esto escala por INTEG-02. Vacío = sin tarifa." />
            </div>
            {formError && <Notice tone="error">{formError}</Notice>}
            <div className="flex flex-wrap items-center justify-end gap-3">
              <button type="button" onClick={closeForm}
                className="px-4 py-2 rounded-xl bg-white border border-brand-border text-xs font-semibold text-brand-navy hover:bg-slate-50">
                Cancelar
              </button>
              <button type="submit" disabled={saving}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-brand-navy hover:bg-brand-steel text-white text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed">
                <span className="material-symbols-outlined text-[16px] text-brand-teal">save</span>
                {saving ? 'Guardando...' : isCreate ? 'Dar de alta' : 'Guardar cambios'}
              </button>
            </div>
          </form>
        )}

        <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-brand-border/60 text-xs">
            <span className="text-brand-muted">{loading ? 'Cargando beneficiarios…' : `${activeCount} activos de ${vendors.length}`}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-[960px] w-full text-left text-xs">
              <thead className="bg-slate-50 text-brand-muted uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-5 py-3 font-semibold">Razón social</th>
                  <th className="px-3 py-3 font-semibold">NIT</th>
                  <th className="px-3 py-3 font-semibold">Cuenta autorizada</th>
                  <th className="px-3 py-3 font-semibold text-right">Tarifa</th>
                  <th className="px-3 py-3 font-semibold">PEP</th>
                  <th className="px-3 py-3 font-semibold">Estado</th>
                  <th className="px-3 py-3 font-semibold">Último cambio</th>
                  <th className="px-5 py-3 font-semibold text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60">
                {vendors.map((v) => (
                  <tr key={v.id} className={v.active ? '' : 'bg-slate-50/70 text-brand-muted'}>
                    <td className="px-5 py-3 font-semibold text-brand-navy">{v.legal_name}</td>
                    <td className="px-3 py-3 font-mono whitespace-nowrap">{v.tax_id}</td>
                    <td className="px-3 py-3 font-mono text-[11px] whitespace-nowrap">{v.bank_account || '—'}</td>
                    <td className="px-3 py-3 font-mono text-right whitespace-nowrap">{v.contract_amount_usd != null ? `${formatUsd(v.contract_amount_usd)} USD` : '—'}</td>
                    <td className="px-3 py-3">
                      {v.is_pep
                        ? <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-semibold">PEP</span>
                        : <span className="text-brand-muted">No</span>}
                    </td>
                    <td className="px-3 py-3">
                      <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold ${v.active ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-slate-100 text-brand-steel border-brand-border'}`}>
                        {v.active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-[11px] whitespace-nowrap">{formatChange(v)}</td>
                    <td className="px-5 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button onClick={() => openForm(v)} disabled={readOnly}
                          className="whitespace-nowrap px-3 py-1 rounded-lg border border-brand-border text-[11px] font-semibold text-brand-navy hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed">
                          Editar
                        </button>
                        <button onClick={() => handleToggle(v)} disabled={readOnly || togglingId === v.id}
                          className={`whitespace-nowrap px-3 py-1 rounded-lg border text-[11px] font-semibold disabled:opacity-50 disabled:cursor-not-allowed ${v.active ? 'border-red-200 text-red-700 hover:bg-red-50' : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'}`}>
                          {togglingId === v.id ? '…' : v.active ? 'Dar de baja' : 'Reactivar'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {!loading && vendors.length === 0 && (
                  <tr><td colSpan={8} className="px-5 py-6 text-center text-brand-muted">Sin beneficiarios registrados: todas las facturas escalan por HITL-02.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  )
}
