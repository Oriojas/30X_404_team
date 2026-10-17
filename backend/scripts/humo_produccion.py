"""
Prueba de humo contra un backend desplegado (Fase 4, F4.5).
Verifica /api/health, toma una foto del saldo (PATCH /api/treasury con el saldo del seed), recorre
TC-01..TC-07 por POST /api/invoices y, con --origen, el preflight de CORS.

La foto del saldo cambia la tesorería del backend: lo aprobado antes (corridas anteriores, Telegram) deja
de comprometer el saldo, para que TC-01 no escale por FIN-01/FIN-03 (Fase 6).

Cada caso usa un Idempotency-Key fijo (humo-tc-01 … humo-tc-07): repetir el humo devuelve las mismas
facturas (200) en vez de crear duplicados que INTEG-01 rechazaría. Esas respuestas son la repetición de
la primera corrida, no una evaluación nueva: el script lo advierte. Para validar el pipeline del deploy
actual hace falta una base recién sembrada (DB_SEED_DEMO=true y las reglas por defecto).
Las facturas creadas quedan en la base y se ven en el dashboard.

Uso (desde backend/):
    python -m scripts.humo_produccion https://<backend>.up.railway.app
    python -m scripts.humo_produccion https://<backend>.up.railway.app --origen https://<frontend>.up.railway.app
"""

import argparse
import sys

import httpx

from scripts.casos_demo import CASOS, SALDO_DEMO_USD

ESTADOS_HUMANOS = {"HUMAN_APPROVED", "HUMAN_REJECTED"}


def revisar_health(client: httpx.Client) -> tuple[bool, str]:
    response = client.get("/api/health")
    try:
        body = response.json() if response.status_code == 200 else {}
    except ValueError:
        body = {}
    ok = isinstance(body, dict) and body.get("status") == "ok" and body.get("database") == "connected"
    return ok, f"HTTP {response.status_code} {body}"


def tomar_foto_del_saldo(client: httpx.Client) -> tuple[bool, str]:
    response = client.patch("/api/treasury", json={"balance_usd": SALDO_DEMO_USD})
    try:
        body = response.json() if response.status_code == 200 else {}
    except ValueError:
        body = {}
    ok = (isinstance(body, dict) and body.get("balance_usd") == SALDO_DEMO_USD
          and body.get("committed_usd") == 0)
    detalle = (f"saldo {body.get('balance_usd')}, comprometido {body.get('committed_usd')}"
               if ok else f"HTTP {response.status_code} {response.text[:120]}")
    return ok, detalle


def revisar_caso(client: httpx.Client, caso: str, estado: str, regla: str | None, payload: dict) -> tuple[bool, str]:
    key = f"humo-{caso.lower()}"
    response = client.post("/api/invoices", json=payload, headers={"Idempotency-Key": key})
    if response.status_code not in (200, 201):
        return False, f"HTTP {response.status_code} {response.text[:120]}"
    try:
        invoice = response.json()
        obtenido = invoice["decision_status"]
        explicacion = invoice.get("audit_explanation") or ""
    except (ValueError, KeyError, TypeError, AttributeError):
        return False, f"respuesta inesperada (HTTP {response.status_code}) {response.text[:120]}"
    # Una repetición devuelve el estado actual: un escalado que ya decidió un humano sigue siendo correcto.
    aceptados = {estado} | (ESTADOS_HUMANOS if estado == "SCALED_TO_HUMAN" else set())
    ok = obtenido in aceptados and (regla is None or regla in explicacion)
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
            resultados.append(("foto", f"saldo {SALDO_DEMO_USD:g}, comprometido 0", *tomar_foto_del_saldo(client)))
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
    repetidos = sum("(HTTP 200)" in obtenido for nombre, _, _, obtenido in resultados if nombre.startswith("TC-"))
    if repetidos:
        print(f"⚠️  {repetidos} caso(s) respondieron 200: son la factura guardada de una corrida anterior "
              "(misma Idempotency-Key), no una evaluación del deploy actual.")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
