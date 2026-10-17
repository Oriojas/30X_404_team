import React from 'react'

export default function AuditTable({ invoices = [] }) {
  const getBadge = (status) => {
    switch (status) {
      case 'AUTO_APPROVED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">Auto-Aprobada</span>
      case 'SCALED_TO_HUMAN':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">Escalada a Humano</span>
      case 'REJECTED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">Rechazada</span>
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800">{status}</span>
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-6">
      <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Panel de Auditoría (Audit Log)</h2>
          <p className="text-xs text-slate-500">Trazabilidad en tiempo real con explicabilidad de decisiones en lenguaje natural</p>
        </div>
        <span className="text-xs bg-[#2B9CAE]/10 text-[#2B9CAE] font-medium px-2.5 py-1 rounded">
          $0.00 FX Markup
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Factura</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Proveedor</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Monto Original</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Equivalente USD</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Estado</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Explicación Audit Log</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {invoices.length === 0 ? (
              <tr>
                <td colSpan="6" className="text-center py-8 text-slate-400">
                  No se han recibido facturas aún. Envía una foto o PDF al bot de Telegram para comenzar.
                </td>
              </tr>
            ) : (
              invoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-800">{inv.invoice_number}</td>
                  <td className="px-4 py-3 text-slate-700">{inv.vendor_name}</td>
                  <td className="px-4 py-3 text-right font-mono text-slate-600">
                    {inv.original_amount?.toLocaleString()} {inv.original_currency}
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-semibold text-slate-800">
                    ${inv.usd_amount?.toFixed(2)} USD
                  </td>
                  <td className="px-4 py-3 text-center">{getBadge(inv.decision_status)}</td>
                  <td className="px-4 py-3 text-xs text-slate-600 max-w-md">{inv.audit_explanation}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
