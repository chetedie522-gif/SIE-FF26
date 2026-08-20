# -*- coding: utf-8 -*-
"""
Sincroniza las compras cargadas en el FORMULARIO PÚBLICO (Supabase) hacia el
registro durable `compras_reg.json`. Reemplaza el paso manual de "pegame el
export de la app" — ahora es 100% automático.

Lee de Supabase solo las filas con sincronizado=false, las agrega al registro
(con código FF26.CP.#### correlativo y el capítulo resuelto desde la partida),
y las marca como sincronizadas para no duplicarlas en la próxima corrida.
"""
import sys, os, json, datetime, requests
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SIE
from _supabase import REST_URL, headers

# service_role: variable de entorno primero (GitHub Actions), si no existe cae al
# archivo local (PC de Nacho) — así el mismo script corre en los dos contextos.
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not SERVICE_ROLE_KEY:
    from _supabase_secret import SERVICE_ROLE_KEY

def admin_headers(prefer=None):
    """service_role: bypassa RLS. Solo para el paso de marcar sincronizado (server-side)."""
    h = {"apikey": SERVICE_ROLE_KEY, "Authorization": "Bearer " + SERVICE_ROLE_KEY,
         "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    return h

REG = os.path.join(SIE, "tablero_economico", "compras_reg.json")
TREE = os.path.join(SIE, "tablero_economico", "partidas_insumos.json")

def n(x):
    try: return float(x)
    except: return 0.0

def cap_de(partida, byPart):
    p = byPart.get(partida)
    return p["cap"] if p else ""

def next_codigo(existentes):
    mx = 0
    for c in existentes:
        cod = c.get("codigo", "")
        if cod.startswith("FF26.CP."):
            try: mx = max(mx, int(cod.split(".")[-1]))
            except ValueError: pass
    return mx

def main():
    try:
        reg = json.load(open(REG, encoding="utf-8"))
    except FileNotFoundError:
        reg = {"obra": "FF26", "actualizado": "", "compras": []}
    tree = json.load(open(TREE, encoding="utf-8"))
    byPart = {p["cod"]: p for p in tree["partidas"]}

    r = requests.get(REST_URL + "/compras", params={"sincronizado": "eq.false", "order": "id.asc"},
                      headers=headers(), timeout=20)
    r.raise_for_status()
    pendientes = r.json()

    if not pendientes:
        print("Sin compras nuevas del formulario web.")
        return 0

    hoy = datetime.date.today().isoformat()
    mx = next_codigo(reg["compras"])
    ids_ok = []
    for row in pendientes:
        mx += 1
        entry = {
            "codigo": f"FF26.CP.{mx:04d}",
            "fecha": row.get("fecha") or hoy,
            "proveedor": row.get("proveedor", ""),
            "cap": cap_de(row.get("partida", ""), byPart),
            "partida": row.get("partida", ""),
            "insumo": row.get("insumo", ""),
            "detalle": row.get("detalle", ""),
            "cant": str(row.get("cant", "")),
            "unidad": row.get("unidad", ""),
            "monto": str(row.get("monto", "")),
            "tipo": row.get("tipo", ""),
            "cond": row.get("cond", ""),
            "estadoPago": row.get("estado_pago") or "Pendiente a autorizar",
            "beneficiario": row.get("beneficiario", ""),
            "medio": row.get("medio", ""),
            "refPago": row.get("concepto", ""),
            "fechaVencimiento": row.get("fecha_vencimiento") or "",
            "factura": row.get("factura", ""),
            "quien": row.get("quien", ""),
            "fcarga": hoy,
        }
        reg["compras"].append(entry)
        ids_ok.append(row["id"])
        print(f"  + {entry['codigo']}  {entry['proveedor']} · {entry['detalle'][:40]} · {entry['monto']} Gs")

    reg["actualizado"] = hoy
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # marcar como sincronizadas (service_role: bypassa RLS, no lo puede hacer la clave pública)
    for rid in ids_ok:
        pr = requests.patch(REST_URL + "/compras", params={"id": f"eq.{rid}"},
                             headers=admin_headers(prefer="return=representation"),
                             json={"sincronizado": True}, timeout=20)
        pr.raise_for_status()
        if not pr.json():
            print(f"   ⚠ ADVERTENCIA: no se pudo confirmar el marcado de sincronizado para id={rid}"
                  " (revisá que _supabase_secret.py tenga la service_role key correcta)")

    print(f"OK · {len(ids_ok)} compra(s) sincronizada(s) al registro.")
    return len(ids_ok)

if __name__ == "__main__":
    main()
