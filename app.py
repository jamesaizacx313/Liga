import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# Configuración inicial de la página móvil/web
st.set_page_config(
    page_title="Liga de Voleibol La Chona",
    page_icon="🏐",
    layout="centered"
)

# Conexión segura a Supabase usando los Secrets de Streamlit
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Descarga optimizada de datos con caché
@st.cache_data
def cargar_datos_torneo():
    res_eq = supabase.table("equipos").select("id, nombre").execute()
    equipos_map = {eq["id"]: eq["nombre"] for eq in res_eq.data}
    res_pt = supabase.table("partidos").select("*").order("jornada").order("hora").order("cancha").execute()
    return equipos_map, res_pt.data

try:
    equipos_map, partidos_data = cargar_datos_torneo()
except Exception as e:
    st.error("❌ Error al conectar con la base de datos.")
    st.stop()

# ==========================================
# 📌 ENTORNO GRÁFICO (CON ASSET WEB SEGURO)
# ==========================================

# Icono de Balón Profesional e hiperrealista directo de la web (100% redondo)
BALON_WEB_IMG = '<img src="https://img.icons8.com/color/96/volleyball.png" width="22" height="22" style="vertical-align: middle; margin-right: 8px; display: inline-block; filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.15));"/>'

# Silbato de Arbitraje nítido para las tarjetas
WHISTLE_SVG = '<svg viewBox="0 0 24 24" width="14" height="14" style="fill: currentColor; vertical-align: middle; margin-right: 6px; display: inline-block;"><path d="M12 3a7 7 0 0 0-6.93 6H2v5h3.07a7 7 0 0 0 11.24 3.73l2.82 2.83 2.12-2.12-2.83-2.82A7 7 0 0 0 12 3zm0 12a5 5 0 1 1 5-5 5 5 0 0 1-5 5z"/></svg>'

CAR_SVG = '<svg viewBox="0 0 24 24" width="13" height="13" style="fill: #38BDF8; vertical-align: middle; margin-left: 5px; display: inline-block;"><path d="M19 15h-1v-3c0-.6-.4-1-1-1H7c-.6 0-1 .4-1 1v3H5c-.6 0-1 .4-1 1v3c0 .6.4 1 1 1h1c0 1.1.9 2 2 2s2-.9 2-2h4c0 1.1.9 2 2 2s2-.9 2-2h1c0 .6.4 1 1 1v-3c0-.6-.4-1-1-1zM7 13h10v2H7v-2z"/></svg>'

# ==========================================
# HEADER RECONSTRUIDO (100% SEGURO)
# ==========================================
HEADER_HTML = f'<div style="text-align: center; margin-bottom: 24px; font-family: system-ui, -apple-system, sans-serif;"><div style="display: inline-flex; align-items: center; background: #1E293B; padding: 6px 18px; border-radius: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #334155; margin-bottom: 12px;">{BALON_WEB_IMG}<span style="color: #F8FAFC; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;">TORNEO OFICIAL 2026</span></div><h1 style="color: #0F172A; font-size: 42px; font-weight: 900; letter-spacing: -1.5px; margin: 0; text-transform: uppercase; line-height: 0.95;">LIGA LA CHONA</h1><div style="width: 60px; height: 4px; background: linear-gradient(90deg, #FF6B35, #D44A1D); margin: 14px auto 0 auto; border-radius: 2px;"></div></div>'

st.markdown(HEADER_HTML, unsafe_allow_html=True)

# ==========================================
# FILTROS INTEGRADOS (MÓVIL-OPTIMIZADO)
# ==========================================
col1, col2 = st.columns(2)
with col1:
    jornadas = sorted(list(set([p["jornada"] for p in partidos_data])))
    opciones_j = ["📅 TODAS LAS JORNADAS"] + [f"📅 JORNADA {j}" for j in jornadas]
    jornada_sel = st.selectbox("j_f", opciones_j, index=1, label_visibility="collapsed")
    jornada_val = "TODAS" if "TODAS" in jornada_sel else int(jornada_sel.split("JORNADA ")[1])

with col2:
    opciones_e = ["🔍 TODOS LOS EQUIPOS"] + sorted(list(equipos_map.values()))
    equipo_sel = st.selectbox("e_f", opciones_e, index=0, label_visibility="collapsed")
    equipo_val = "VER TODO" if "TODOS" in equipo_sel else equipo_sel

# ==========================================
# LOGICA DE RENDERIZADO DE FILAS Y TARJETAS
# ==========================================
def obtener_html_tarjeta(partido, eq_filtro):
    if not partido:
        return '<div style="flex: 1; background-color: #0B0F19; border: 1px dashed #232D42; border-radius: 12px; display: flex; justify-content: center; align-items: center; color: #475569; font-size: 12px; font-style: italic; min-height: 76px; box-sizing: border-box;">🌙 Cerrado</div>'
    
    loc, vis = equipos_map.get(partido["equipo_local_id"]), equipos_map.get(partido["equipo_visita_id"])
    arb = equipos_map.get(partido["equipo_arbitro_id"], "Sin Árbitro")
    juega = (loc == eq_filtro or vis == eq_filtro) and eq_filtro != "VER TODO"
    pita = (arb == eq_filtro) and eq_filtro != "VER TODO"
    
    html_arb = f'<span style="color: #2ECC71; font-weight: 800;">{WHISTLE_SVG} PITA: {arb.upper()}</span>' if pita else f'{WHISTLE_SVG} Pita: <span style="color: #94A3B8;">{arb}</span>'
    
    if juega:
        estilo = "background: linear-gradient(135deg, rgba(255,107,53,0.18) 0%, rgba(212,74,29,0.06) 100%); border: 2px solid #FF6B35; box-shadow: 0 0 15px rgba(255,107,53,0.1);"
        vs_b = 'background-color: #FF6B35; color: #0B0F19;'
    elif pita:
        estilo = "background: linear-gradient(135deg, rgba(46,204,113,0.15) 0%, rgba(46,204,113,0.04) 100%); border: 2px solid #2ECC71;"
        vs_b = 'background-color: #232D42; color: #94A3B8;'
    else:
        estilo = "background-color: #131B2E; border: 1px solid #232D42;"
        vs_b = 'background-color: #232D42; color: #94A3B8;'

    return f"""
    <div style="flex: 1; {estilo} border-radius: 12px; padding: 14px 12px; display: flex; flex-direction: column; justify-content: space-between; min-height: 76px; box-sizing: border-box;">
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 6px;">
            <div style="flex: 1; text-align: right; font-size: 13px; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #FFFFFF;">{loc}</div>
            <div style="{vs_b} font-size: 9px; font-weight: 900; padding: 2px 5px; border-radius: 4px; flex-shrink: 0; letter-spacing: 0.5px;">VS</div>
            <div style="flex: 1; text-align: left; font-size: 13px; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #FFFFFF;">{vis}{CAR_SVG if "lagos" in vis.lower() else ""}</div>
        </div>
        <div style="margin-top: 8px; text-align: center; font-size: 11px; color: #64748B; font-weight: 600; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 6px;">{html_arb}</div>
    </div>
    """

def generar_html_jornada(j_num):
    partidos = [p for p in partidos_data if p["jornada"] == int(j_num)]
    tiene_lagos = any("lagos" in equipos_map.get(p["equipo_visita_id"], "").lower() for p in partidos)
    estatus = "⚡ JORNADA ESPECIAL: Lagos de visita (Franja 9 PM Activa)" if tiene_lagos else "🏠 OPERACIÓN REGULAR: Cierre 10:00 PM"
    
    bloques = ""
    for h in ["7:00 PM", "8:00 PM", "9:00 PM"]:
        p_hora = [p for p in partidos if p["hora"] == h]
        p_c1 = next((p for p in p_hora if p["cancha"] == "Cancha 1"), None)
        p_c2 = next((p for p in p_hora if p["cancha"] == "Cancha 2"), None)
        if h == "9:00 PM" and not p_c1 and not p_c2: continue
        bloques += f"""
        <div style="display: flex; align-items: center; gap: 12px; width: 100%;">
            <div style="width: 70px; background-color: #131B2E; border: 1px solid #232D42; text-align: center; padding: 10px 0; border-radius: 10px; font-weight: 800; font-size: 12px; color: #FF6B35; flex-shrink: 0;">🕒 {h.replace(' PM', '')}</div>
            {obtener_html_tarjeta(p_c1, equipo_val)}
            {obtener_html_tarjeta(p_c2, equipo_val)}
        </div>"""
        
    return f"""
    <div style="font-family: system-ui, -apple-system, sans-serif; background-color: #060B14; padding: 16px; border-radius: 16px; margin-bottom: 24px; border: 1px solid #131B2E; box-shadow: 0 10px 30px rgba(0,0,0,0.35); width: 100%; box-sizing: border-box;">
        <div style="text-align: center; border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 14px;">
            <div style="font-size: 20px; font-weight: 900; color: #FF6B35; text-transform: uppercase; letter-spacing: 0.5px;">JORNADA {j_num}</div>
            <div style="font-size: 11px; color: #38BDF8; font-weight: 700; margin-top: 3px; letter-spacing: 0.5px;">{estatus}</div>
        </div>
        <div style="display: flex; gap: 12px; margin-bottom: 10px; text-align: center; opacity: 0.9;">
            <div style="width: 70px; flex-shrink: 0;"></div>
            <div style="flex: 1; color: #4A90E2; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Cancha 1</div>
            <div style="flex: 1; color: #4A90E2; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Cancha 2</div>
        </div>
        <div style="display: flex; flex-direction: column; gap: 12px;">{bloques}</div>
    </div>"""

# ==========================================
# ENSAMBLADO Y AJUSTE DE ALTURA FIJA
# ==========================================
pizarra = '<div style="width: 100%; box-sizing: border-box; padding: 2px;">'
if jornada_val == "TODAS":
    for j in jornadas: pizarra += generar_html_jornada(j)
    h_c = 2800
else:
    pizarra += generar_html_jornada(jornada_val)
    h_c = 445
pizarra += '</div>'

components.html(pizarra, height=h_c, scrolling=True)