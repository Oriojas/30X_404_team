"""
Prueba de humo contra un backend desplegado (Fase 4, F4.5).
Verifica /api/health, recorre TC-01..TC-06 por POST /api/invoices y, con --origen, el preflight de CORS.

Cada caso usa un Idempotency-Key fijo (humo-tc-01 … humo-tc-06): repetir el humo devuelve las mismas
facturas (200) en vez de crear duplicados que INTEG-01 rechazaría.
Requiere una base con el seed de demostración (DB_SEED_DEMO=true) y las reglas por defecto.

Uso (desde backend/):
    python -m scripts.humo_produccion https://<backend>.up.railway.app
    python -m scripts.humo_produccion https://<backend>.up.railway.app --origen https://<frontend>.up.railway.app
"""

import argparse
import sys

import httpx

# Mismos payloads que tests/test_postgres_integration.py.
CASOS = [
    ("TC-01", "AUTO_APPROVED", None, {
        "invoice_number": "AWS-2026-10", "vendor_name": "Amazon Web Services LATAM",
        "vendor_tax_id": "US-91-1646860", "original_amount": 450}),
    ("TC-02", "REJECTED", "INTEG-01", {
        "invoice_number": "DS-1042", "vendor_name": "DevStudio LatAm S.A.S.",
        "vendor_tax_id": "900.584.112-4", "original_amount": 5040000, "original_currency": "COP"}),
    ("TC-03", "SCALED_TO_HUMAN", "HITL-02", {
        "invoice_number": "DC-001", "vendor_name": "Diseño Creativo Bogotá S.A.S.", "original_amount": 800}),
    ("TC-04", "SCALED_TO_HUMAN", "HITL-01", {
        "invoice_number": "NA-090", "vendor_name": "Nube Andina Consultores S.A.S.",
        "vendor_tax_id": "901.223.450-1", "original_amount": 3500}),
    ("TC-05", "SCALED_TO_HUMAN", "FIN-01", {
        "invoice_number": "LEM-3400", "vendor_name": "Logística Express MX S.A. de C.V.",
        "vendor_tax_id": "LEM850101AB1", "original_amount": 195000, "original_currency": "MXN"}),
    ("TC-06", "REJECTED", "COMP-01", {
        "invoice_number": "GTP-01", "vendor_name": "Global Trade Partners Ltd",
        "vendor_tax_id": "PA-155-7788", "bank_account": "PA-BANCO-PACIFICO-998877", "original_amount": 900}),
]


def revisar_health(client: httpx.Client) -> tuple[bool, str]:
    response = client.get("/api/health")
    body = response.json() if response.status_code == 200 else {}
    ok = body.get("status") == "ok" and body.get("database") == "connected"
    return ok, f"HTTP {response.status_code} {body}"


def revisar_caso(client: httpx.Client, caso: str, estado: str, regla: str | None, payload: dict) -> tuple[bool, str]:
    key = f"humo-{caso.lower()}"
    response = client.post("/api/invoices", json=payload, headers={"Idempotency-Key": key})
    if response.status_code not in (200, 201):
        return False, f"HTTP {response.status_code} {response.text[:120]}"
    invoice = response.json()
    obtenido = invoice["decision_status"]
    ok = obtenido == estado and (regla is None or regla in invoice["audit_explanation"])
    return ok, f"{obtenido} (HTTP {response.status_code})"


def revisar_reglas(client: httpx.Client) -> tuple[bool, str]:
    response = client.get("/api/rules")
    return response.status_code == 200, f"HTTP {response.status_code}"


def revisar_cors(client: httpx.Client, origen: str) -> tuple[bool, str]:
    response = client.options("/api/invoices", headers={
        "Origin": origen, "Access-Control-Request-Method": "POST"})
    permitido = response.headers.get("access-control-allow-origin")
    return permitido == origen, f"allow-origin={permitido}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url_base", help="URL del backend, p. ej. https://backend.up.railway.app")
    parser.add_argument("--origen", help="dominio del frontend para comprobar CORS")
    args = parser.parse_args()

    resultados = []
    with httpx.Client(base_url=args.url_base.rstrip("/"), timeout=60) as client:
        try:
            resultados.append(("health", "ok + connected", *revisar_health(client)))
            for caso, estado, regla, payload in CASOS:
                esperado = estado + (f" + {regla}" if regla else "")
                resultados.append((caso, esperado, *revisar_caso(client, caso, estado, regla, payload)))
            resultados.append(("rules", "HTTP 200", *revisar_reglas(client)))
            if args.origen:
                resultados.append(("cors", args.origen, *revisar_cors(client, args.origen)))
        except httpx.HTTPError as error:
            sys.exit(f"No se pudo conectar con {args.url_base}: {error}")

    for nombre, esperado, ok, obtenido in resultados:
        print(f"{'✅' if ok else '❌'} {nombre:7} esperado: {esperado:32} obtenido: {obtenido}")
    fallos = sum(not ok for _, _, ok, _ in resultados)
    print(f"\n{len(resultados) - fallos}/{len(resultados)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
