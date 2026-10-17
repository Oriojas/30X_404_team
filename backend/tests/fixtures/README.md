# Facturas de prueba (ficticias)

Documentos inventados para probar el OCR con Gemini. Los proveedores existen en `seed.sql`, pero los números de factura no, así que no chocan con INTEG-01.
En las dos facturas colombianas la moneda solo aparece como `$`: el modelo debe deducir `COP` por el NIT y la ciudad. La de Global Trade Partners es el caso TC-06: proveedor y cuenta en la lista OFAC del seed.

| Archivo | Número | Proveedor (NIT) | Monto esperado | Moneda | Vencimiento | Cuenta | Decisión esperada con el seed de demo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `factura_devstudio.png` | `DS-2026-1107` | DevStudio LatAm S.A.S. (`900.584.112-4`) | `4200000.0` (`$ 4.200.000,00`) | `COP` | `2026-11-30` | `CO-BANCOLOMBIA-11122233344` | `AUTO_APPROVED` (1.000 USD, dentro del contrato y del límite autónomo) |
| `factura_nube_andina.pdf` | `NA-4521` | Nube Andina Consultores S.A.S. (`901.223.450-1`) | `12600000.0` (`$ 12.600.000`) | `COP` | `2026-12-05` | `CO-DAVIVIENDA-55566677788` | `SCALED_TO_HUMAN` por HITL-01 (3.000 USD supera el límite de 2.000) |
| `factura_global_trade.png` | `GTP-0091` | Global Trade Partners Ltd (`PA-155-7788`) | `900.0` (`US$ 900.00`) | `USD` | `2026-11-20` | `PA-BANCO-PACIFICO-998877` | `REJECTED` por COMP-01 (coincidencia con lista OFAC) |

`tests/test_postgres_integration.py` sube las tres por la API contra PostgreSQL con el seed (cliente de Gemini simulado) y verifica estas decisiones cuando existe `TEST_DATABASE_URL`.

Prueba manual con una `GEMINI_API_KEY` real:

```bash
curl -F "file=@backend/tests/fixtures/factura_devstudio.png" http://localhost:8000/api/invoices/upload
```
