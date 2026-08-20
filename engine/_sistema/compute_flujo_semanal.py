# -*- coding: utf-8 -*-
"""
Flujo de caja semanal: columnas = semanas (agrupadas por mes), filas = producción
pendiente por rubro (repartida entre las semanas reales del cronograma en que ese
rubro tiene tareas) + gastos comprometidos/cheques a vencer (fecha real de pago).

Fuente del cronograma: tablero_economico/cronograma.json (extraído una vez de
Cronograma_FF2026_EDITABLE1.xlsx — re-extraer a mano si el cronograma cambia).
Escribe el resultado dentro de economia.json (clave "flujo_semanal").
"""
import json, os, datetime as dt
from _paths import SIE

base = os.path.join(SIE, "tablero_economico")
eco = json.load(open(os.path.join(base, "economia.json"), encoding="utf-8"))
crono = json.load(open(os.path.join(base, "cronograma.json"), encoding="utf-8"))
try:
    compras = json.load(open(os.path.join(base, "compras_reg.json"), encoding="utf-8"))["compras"]
except FileNotFoundError:
    compras = []

def n(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0

semanas = crono["semanas"]  # [{"semana":0,"fecha":"2026-08-10","mes":"AGOSTO 2026"}, ...]
fechas = [dt.date.fromisoformat(s["fecha"]) for s in semanas]

def semana_de(fecha_iso):
    """Última semana cuyo inicio es <= fecha (clampeado al rango del cronograma)."""
    try: d = dt.date.fromisoformat(fecha_iso)
    except (ValueError, TypeError): return len(semanas) - 1
    idx = 0
    for i, f in enumerate(fechas):
        if f <= d: idx = i
        else: break
    return idx

def pago_date(fecha, cond, vencimiento):
    if vencimiento:
        try: return vencimiento
        except (ValueError, TypeError): pass
    try: d = dt.date.fromisoformat(fecha)
    except (ValueError, TypeError): return fecha
    cl = (cond or "").lower()
    if "crédit" in cl or "credit" in cl or "cheque dif" in cl:
        return (d + dt.timedelta(days=30)).isoformat()
    return fecha

# --- producción pendiente por rubro, repartida en sus semanas activas ---
filas = []
for cap in eco["capitulos"]:
    semanas_activas = crono["cap_semanas"].get(cap["cap"], [])
    pendiente = max(0, cap["objetivo"] - cap["comprometido"])
    valores = [0.0] * len(semanas)
    if semanas_activas:
        porSemana = pendiente / len(semanas_activas)
        idx_por_semana = {s["semana"]: i for i, s in enumerate(semanas)}
        for sn in semanas_activas:
            i = idx_por_semana.get(sn)
            if i is not None: valores[i] += porSemana
    filas.append({"cap": cap["cap"], "nombre": cap["nombre"], "valores": [round(v) for v in valores]})

# --- gastos comprometidos / cheques a vencer, por semana real ---
gastos = [0.0] * len(semanas)
for c in compras:
    pd = pago_date(c.get("fecha"), c.get("cond"), c.get("fechaVencimiento"))
    i = semana_de(pd)
    gastos[i] += n(c.get("monto"))
gastos = [round(v) for v in gastos]

eco["flujo_semanal"] = {"semanas": semanas, "filas": filas, "gastos": gastos}
json.dump(eco, open(os.path.join(base, "economia.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("OK flujo_semanal ·", len(semanas), "semanas ·", len(filas), "rubros")
print("Gastos comprometidos por semana:", gastos)
