# -*- coding: utf-8 -*-
import json, sys, datetime as dt
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SIE
eco = json.load(open(SIE + "/tablero_economico/economia.json", encoding="utf-8"))
try: compras = json.load(open(SIE + "/tablero_economico/compras_reg.json", encoding="utf-8"))["compras"]
except: compras = []
HOY = dt.date(2026,8,18)

adicionales = eco["resumen"].get("adicionales", [])
adObj = sum(a["objetivo_con_iva"] for a in adicionales)
adVenta = sum(a["venta_con_iva"] for a in adicionales)
objTotal = eco["resumen"]["objetivo_con_iva"] + adObj  # egreso total con IVA (base + adicionales)
contrato = eco["resumen"]["contrato_con_iva"] + adVenta
def n(x):
    try: return float(x)
    except: return 0.0

meses = ["2026-08","2026-09","2026-10","2026-11","2026-12","2027-01","2027-02"]
mk = lambda d: f"{d.year}-{d.month:02d}"

# curva de egreso del objetivo (según cronograma) — pesos por mes
E = {"2026-08":80830572,"2026-09":155339677,"2026-10":173009036,"2026-11":351916866,"2026-12":261858680,"2027-01":4964901,"2027-02":0}
# AD1: ejecución asumida sep (60%) / oct (40%) — mismo reparto que su cobro
E["2026-09"] += round(adObj*0.6); E["2026-10"] += round(adObj*0.4)
totE = sum(E.values())

# cobros: cronograma de pagos del cliente (con IVA)
DES = [["2026-08-14",287950230],["2026-08-21",35993779],["2026-08-28",35993779],["2026-09-04",35993778],["2026-09-11",35993779],["2026-09-18",35993779],["2026-09-25",179968894],["2026-10-02",35993778],["2026-10-09",35993779],["2026-10-16",35993779],["2026-10-23",35993779],["2026-10-30",179968893],["2026-11-06",35993779],["2026-11-13",35993779],["2026-11-20",35993779],["2026-11-27",143975115],["2026-12-04",35993778],["2026-12-11",35993779],["2026-12-18",143975115]]
# ADICIONAL AD1: 60% inicio / 40% término (fechas asumidas — ajustar con el plan real)
DES += [["2026-09-07",81118800],["2026-10-12",54079200]]
ing = {m:0.0 for m in meses}
for f,mo in DES:
    k = f[:7]
    if k in ing: ing[k]+=mo

# egresos REALES por fecha de pago. Prioridad: fecha_vencimiento explícita
# (cheque marcado a mano) > estimación por condición (crédito 30d / cheque dif → +30 días)
def pago_date(fecha, cond, vencimiento):
    if vencimiento:
        try: return dt.date.fromisoformat(vencimiento)
        except: pass
    try: d = dt.date.fromisoformat(fecha)
    except: d = HOY
    cl = (cond or "").lower()
    if "crédit" in cl or "credit" in cl or "cheque dif" in cl: return d + dt.timedelta(days=30)
    return d
egr_real = {m:0.0 for m in meses}
comprometido = 0.0
for c in compras:
    comprometido += n(c.get("monto"))
    k = mk(pago_date(c.get("fecha"), c.get("cond"), c.get("fechaVencimiento")))
    if k in egr_real: egr_real[k]+=n(c.get("monto"))
    else: egr_real[meses[-1]]+=n(c.get("monto"))

# resto del objetivo (no comprado) distribuido por la curva del cronograma
resto = max(0, objTotal - comprometido)
egr = {}
for m in meses:
    egr[m] = round(egr_real[m] + resto*(E.get(m,0)/totE))

# armar flujo acumulado
flujo=[]; ia=ea=0.0; lo=None
for m in meses:
    ia+=ing[m]; ea+=egr[m]; neto=ia-ea
    row={"mes":m,"ingreso":round(ing[m]),"egreso":egr[m],"ing_acum":round(ia),"egr_acum":round(ea),"neto_acum":round(neto)}
    flujo.append(row)
    if lo is None or neto<lo["neto_acum"]: lo=row
# recortar meses finales sin movimiento
while len(flujo)>1 and flujo[-1]["ingreso"]==0 and flujo[-1]["egreso"]==0:
    flujo.pop()

eco["flujo"]=flujo
eco["flujo_supuesto"]=False
eco["esquema_cobro"]="EN VIVO · cobros = cronograma del cliente · egresos reales por fecha de pago (crédito 30d = +30 días) + resto del objetivo según cronograma"
eco["resumen"]["comprometido"]=round(comprometido)
eco["pico_exposicion"]={"mes":lo["mes"],"monto":lo["neto_acum"]}
json.dump(eco, open(SIE + "/tablero_economico/economia.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)

print("Flujo en vivo (con IVA):")
for f in flujo: print(f"  {f['mes']}: ing {f['ingreso']:>13,} egr {f['egreso']:>13,} neto_acum {f['neto_acum']:>13,}")
print(f"\nComprometido: {round(comprometido):,} · resto objetivo: {round(resto):,}")
print(f"Punto más bajo de caja: {lo['neto_acum']:,} en {lo['mes']}")
