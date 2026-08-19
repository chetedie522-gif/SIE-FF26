# -*- coding: utf-8 -*-
"""
Genera el FORMULARIO PÚBLICO de carga de compras (reemplaza la app-Artifact).
Escribe directo a Supabase por fetch() desde el navegador — sin backend propio,
sin login. Vive en el sitio como cualquier otro tablero: `/compras/`.

Sale desde el mismo partidas_app.json que usaba la app vieja (desplegable
partida -> insumo). Fuente: build_site.py lo copia a site/compras/index.html.
"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SYS
from _supabase import SUPABASE_URL, SUPABASE_ANON_KEY

data = json.load(open(SYS + "/partidas_app.json", encoding="utf-8"))
DATA = json.dumps(data, ensure_ascii=False)

HTML = r'''<title>Cargar compras · FF26</title>
<style>
:root{--bg:#12161c;--card:#1b212a;--card2:#212a35;--line:#2c3540;--txt:#e8ecf1;--mut:#8c98a8;--ok:#2fa76a;--warn:#d9a020;--bad:#e0555f;--acc:#5b8fd6}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:14px;max-width:720px;margin:0 auto}
h1{font-size:19px}.sub{color:var(--mut);font-size:12.5px;margin:2px 0 14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--mut);margin-bottom:12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
label{display:block;font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
input,select{width:100%;background:var(--card2);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:9px 10px;font-size:14px}
.full{grid-column:1/-1}
button.main{background:var(--acc);color:#fff;border:none;border-radius:8px;padding:11px 18px;font-size:14px;font-weight:700;cursor:pointer;margin-top:12px;width:100%}
button.main:disabled{opacity:.5;cursor:default}
.hint{color:var(--mut);font-size:11px;margin-top:2px}
.msg{border-radius:8px;padding:10px 12px;font-size:13px;margin-top:12px;display:none}
.msg.ok{background:rgba(47,167,106,.14);border:1px solid rgba(47,167,106,.4);color:#8fe0b6;display:block}
.msg.bad{background:rgba(224,85,95,.14);border:1px solid rgba(224,85,95,.4);color:#f0a8ad;display:block}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;color:var(--mut);font-weight:600;padding:6px 8px;border-bottom:1px solid var(--line);font-size:10px}
td{padding:6px 8px;border-bottom:1px solid var(--card2)}
.empty{color:var(--mut);font-style:italic;font-size:13px}
a.back{color:var(--acc);text-decoration:none;font-size:13px}
</style>

<a class="back" href="../">← volver al hub</a>
<h1>🛒 Cargar compra — Obra FF26</h1>
<div class="sub">Nave Ampliación 20x35 · se guarda directo, el sitio se actualiza en un rato</div>

<div class="card">
  <h2>➕ Nueva compra</h2>
  <div class="g3">
    <div><label>Proveedor</label><input id="proveedor" placeholder="ej. Hierro Matt"></div>
    <div><label>N° de factura</label><input id="factura" placeholder="ej. 001-0012345"></div>
    <div><label>Fecha</label><input id="fecha" type="date"></div>
  </div>
  <div class="grid" style="margin-top:10px">
    <div class="full"><label>Partida (capítulo)</label><select id="partida"></select></div>
    <div class="full"><label>Insumo dentro de la partida</label><select id="insumo" disabled><option value="">— elegí primero la partida —</option></select><div class="hint" id="hint"></div></div>
    <div class="full"><label id="lbldesc">Detalle (opcional)</label><input id="detalle" placeholder="marca / observación"></div>
    <div><label>Cantidad</label><input id="cant" inputmode="decimal" placeholder="ej. 40"></div>
    <div><label>Unidad</label><input id="unidad" placeholder="auto del insumo"></div>
    <div class="full"><label>Tipo</label><select id="tipo"><option>Material</option><option>Subcontrato</option><option>Alquiler de equipo</option><option>Mano de obra</option><option>Otro</option></select></div>
    <div><label>Condición de pago</label><select id="cond"><option>Contado</option><option>Crédito 30 días (cheque)</option><option>Cheque diferido</option><option>Adelanto (antes de entrega)</option></select></div>
    <div><label>¿Quién carga?</label><select id="quien"><option>Nancy</option><option>Meli</option><option>Nacho</option><option>Elias</option><option>Otro</option></select></div>
    <div class="full"><label>MONTO total (Gs, con IVA)</label><input id="monto" inputmode="numeric" placeholder="ej. 3.200.000"></div>
  </div>
  <button class="main" id="ok">Registrar compra</button>
  <div class="msg" id="msg"></div>
</div>

<div class="card">
  <h2>📋 Últimas compras cargadas (esta sesión)</h2>
  <div id="recientesWrap"><div class="empty">Todavía no cargaste nada en esta sesión.</div></div>
</div>

<script>
const SUPABASE_URL = "__SB_URL__";
const SUPABASE_ANON_KEY = "__SB_KEY__";
const D = __DATA__;
const byId = Object.fromEntries(D.partidas.map(p=>[p.id,p]));
const f2 = n => new Intl.NumberFormat('es-PY').format(Math.round(n));
const fc = n => { const x=Number(n); return isFinite(x)?(Math.round(x*100)/100).toString():(n||''); };
const hoy = () => new Date().toISOString().slice(0,10);
document.getElementById('fecha').value = hoy();

const selP=document.getElementById('partida'), selI=document.getElementById('insumo');
selP.innerHTML='<option value="">— elegí la partida —</option>';
for(const [c,nom] of Object.entries(D.caps)){
  const og=document.createElement('optgroup'); og.label=nom;
  D.partidas.filter(p=>p.cap===c).forEach(p=>{const o=document.createElement('option');o.value=p.id;o.textContent=`${p.cod} · ${p.desc}`;og.appendChild(o);});
  selP.appendChild(og);
}
selP.addEventListener('change',()=>{
  const p=byId[selP.value]; selI.innerHTML='';
  if(!p){selI.disabled=true;selI.innerHTML='<option value="">— elegí primero la partida —</option>';return;}
  selI.disabled=false;
  selI.appendChild(new Option('— elegí el insumo —',''));
  p.ins.forEach(i=>{const o=new Option(`${i.cod} · ${i.desc}`+(i.cant?` · obj ${fc(i.cant)} ${i.un||''}`:''),i.cod);selI.appendChild(o);});
  selI.appendChild(new Option('➕ nuevo insumo (no previsto)','NUEVO'));
  hintUpd();
});
selI.addEventListener('change',hintUpd);
function hintUpd(){
  const p=byId[selP.value],v=selI.value,lbl=document.getElementById('lbldesc'),h=document.getElementById('hint'),un=document.getElementById('unidad');
  if(v==='NUEVO'){lbl.textContent='Descripción del insumo NUEVO (obligatorio)';h.textContent='Se imputa como no previsto → aparecerá como desvío.';un.value='';un.readOnly=false;}
  else{lbl.textContent='Detalle (opcional)';const i=p&&p.ins.find(x=>x.cod===v);
    h.textContent=i&&i.cant?`Objetivo planificado: ${fc(i.cant)} ${i.un||''}`:'';
    if(i){un.value=i.un||'';} else {un.value='';}}
}
const lm=document.getElementById('monto');
lm.addEventListener('input',()=>{const d=lm.value.replace(/[^0-9]/g,'');lm.value=d?f2(parseInt(d,10)):'';});

let recientes=[];
function renderRecientes(){
  const w=document.getElementById('recientesWrap');
  if(!recientes.length){w.innerHTML='<div class="empty">Todavía no cargaste nada en esta sesión.</div>';return;}
  let h='<table><thead><tr><th>Proveedor</th><th>Partida</th><th>Detalle</th><th>Monto</th></tr></thead><tbody>';
  recientes.forEach(r=>{h+=`<tr><td>${r.proveedor}</td><td>${r.partida}</td><td>${r.detalle||r.insumo}</td><td>${f2(r.monto)}</td></tr>`;});
  h+='</tbody></table>';
  w.innerHTML=h;
}

document.getElementById('ok').addEventListener('click', async ()=>{
  const btn=document.getElementById('ok'), msg=document.getElementById('msg');
  const p=byId[selP.value], ins=selI.value, detalle=document.getElementById('detalle').value.trim();
  const monto=parseFloat((lm.value||'').replace(/[^0-9]/g,''));
  const proveedor=document.getElementById('proveedor').value.trim();
  if(!proveedor){alert('Poné el proveedor.');return;}
  if(!p){alert('Elegí la partida.');return;}
  if(!ins){alert('Elegí el insumo (o "nuevo insumo").');return;}
  if(ins==='NUEVO'&&!detalle){alert('Poné la descripción del insumo nuevo.');return;}
  if(!monto){alert('Poné el monto.');return;}

  const body={
    fecha: document.getElementById('fecha').value||hoy(),
    proveedor, partida: p.cod, insumo: ins, detalle,
    cant: document.getElementById('cant').value.trim(),
    unidad: document.getElementById('unidad').value.trim(),
    monto, tipo: document.getElementById('tipo').value,
    cond: document.getElementById('cond').value,
    quien: document.getElementById('quien').value,
    factura: document.getElementById('factura').value.trim(),
  };
  btn.disabled=true; btn.textContent='Guardando...'; msg.className='msg';
  try{
    const r = await fetch(SUPABASE_URL + '/rest/v1/compras', {
      method:'POST',
      headers:{'apikey':SUPABASE_ANON_KEY,'Authorization':'Bearer '+SUPABASE_ANON_KEY,
               'Content-Type':'application/json','Prefer':'return=minimal'},
      body: JSON.stringify(body)
    });
    if(!r.ok) throw new Error('HTTP '+r.status);
    msg.className='msg ok'; msg.textContent='✓ Compra registrada. El sitio se va a actualizar en un rato (automático).';
    recientes.unshift(body); renderRecientes();
    ['detalle','cant','factura'].forEach(id=>document.getElementById(id).value='');
    lm.value=''; selP.value=''; selI.value=''; selI.disabled=true;
    selI.innerHTML='<option value="">— elegí primero la partida —</option>';
    document.getElementById('hint').textContent='';
    document.getElementById('proveedor').focus();
  }catch(e){
    msg.className='msg bad'; msg.textContent='✗ No se pudo guardar. Revisá tu conexión e intentá de nuevo. ('+e.message+')';
  }finally{
    btn.disabled=false; btn.textContent='Registrar compra';
  }
});
</script>'''

out = HTML.replace("__DATA__", DATA).replace("__SB_URL__", SUPABASE_URL).replace("__SB_KEY__", SUPABASE_ANON_KEY)
outp = SYS + "/compras_ff26.html"
open(outp, "w", encoding="utf-8").write(out)
print("OK · compras_ff26.html ·", len(out), "bytes ·", len(data["partidas"]), "partidas")
