# -*- coding: utf-8 -*-
"""
Copia (engine/) para GitHub Actions: solo actualiza la plantilla del tablero
(FALLBACK embebido). NO toca el Artifact de Claude — ese publish target no
existe en este contexto; se actualiza aparte, manualmente, si hace falta.
"""
import json, re, os
from _paths import SIE
base = os.path.join(SIE, "tablero_pendientes")

data = json.load(open(os.path.join(base, "pendientes.json"), encoding="utf-8"))
compact = json.dumps(data, ensure_ascii=False)

oned = os.path.join(base, "index.html")
s = open(oned, encoding="utf-8").read()
s2 = re.sub(r"const FALLBACK = \{.*?\};", "const FALLBACK = " + compact + ";", s, count=1, flags=re.S)
open(oned, "w", encoding="utf-8").write(s2)
print("tablero_pendientes/index.html:", "actualizado" if s2 != s else "SIN CAMBIO")
