import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# Configuración inicial de la página móvil/web
st.set_page_config(
    page_title="Liga de Voleibol La Chona",
    page_icon="🏐",
    layout="centered"
)

# ==========================================
# 🛑 OCULTAR ELEMENTOS NATIVOS DE STREAMLIT
# ==========================================
st.markdown("""
    <style>
        [data-testid="stHeader"] { visibility: hidden; display: none; }
        footer { visibility: hidden; display: none; }
        #MainMenu { visibility: hidden; display: none; }
        .stDeployButton { display: none; }
    </style>
""", unsafe_allow_html=True)

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
# 📌 ASSETS GRÁFICOS VECTORIALES
# ==========================================
BALON_WEB_IMG = '<img src="https://img.icons8.com/color/96/volleyball.png" width="22" height="22" style="vertical-align: middle; margin-right: 8px; display: inline-block; filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.15));"/>'
WHISTLE_SVG = '<svg viewBox="0 0 24 24" width="13" height="13" style="fill: currentColor; vertical-align: middle; margin-right: 6px; display: inline-block;"><path d="M12 3a7 7 0 0 0-6.93 6H2v5h3.07a7 7 0 0 0 11.24 3.73l2.82 2.83 2.12-2.12-2.83-2.82A7 7 0 0 0 12 3zm0 12a5 5 0 1 1 5-5 5 5 0 0 1-5 5z"/></svg>'
CAR_SVG = '<svg viewBox="0 0 24 24" width="13" height="13" style="fill: #38BDF8; vertical-align: middle; margin-left: 5px; display: inline-block;"><path d="M19 15h-1v-3c0-.6-.4-1-1-1H7c-.6 0-1 .4-1 1v3H5c-.6 0-1 .4-1 1v3c0 .6.4 1 1 1h1c0 1.1.9 2 2 2s2-.9 2-2h4c0 1.1.9 2 2 2s2-.9 2-2h1c0 .6.4 1 1 1v-3c0-.6-.4-1-1-1zM7 13h10v2H7v-2z"/></svg>'

# Hoja de estilos responsiva con fijación de simetría simétrica
CSS_HOJA_ESTILOS = """
<style>
  .pizarra-body { margin: 0; padding: 2px; font-family: system-ui, -apple-system, sans-serif; background-color: transparent; }
  .jornada-container { background-color: #060B14; padding: 16px; border-radius: 16px; margin-bottom: 24px; border: 1px solid #131B2E; box-shadow: 0 10px 30px rgba(0,0,0,0.35); width: 100%; box-sizing: border-box; }
  .jornada-header { text-align: center; border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 14px; }
  .jornada-title { font-size: 20px; font-weight: 900; color: #FF6B35; text-transform: uppercase; letter-spacing: 0.5px; }
  .jornada-status { font-size: 11px; color: #38BDF8; font-weight: 700; margin-top: 3px; letter-spacing: 0.5px; }
  .cancha-headers { display: flex; gap: 12px; margin-bottom: 10px; text-align: center; opacity: 0.9; }
  .cancha-header-space { width: 70px; flex-shrink: 0; }
  .cancha-title { flex: 1; color: #4A90E2; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
  .rows-container { display: flex; flex-direction: column; gap: 12px; }
  .match-row { display: flex; align-items: center; gap: 12px; width: 100%; }
  .time-block { width: 70px; background-color: #131B2E; border: 1px solid #232D42; text-align: center; padding: 10px 0; border-radius: 10px; font-weight: 800; font-size: 12px; color: #FF6B35; flex-shrink: 0; }
  .cards-wrapper { display: flex; gap: 12px; flex: 1; min-width: 0; }
  .match-card { flex: 1; border-radius: 12px; padding: 14px 12px; display: flex; flex-direction: column; justify-content: space-between; min-height: 76px; box-sizing: border-box; min-width: 0; }
  .cancha-badge { display: none; }
  
  /* Variantes de Tarjetas (Fijación de proporción equilibrada) */
  .card-closed { flex: 1; min-width: 0; background-color: #0B0F19; border: 1px dashed #232D42; border-radius: 12px; display: flex; justify-content: center; align-items: center; color: #475569; font-size: 12px; font-style: italic; min-height: 76px; box-sizing: border-box; }
  .card-juega { background: linear-gradient(135deg, rgba(255,107,53,0.18) 0%, rgba(212,74,29,0.06) 100%); border: 2px solid #FF6B35; box-shadow: 0 0 15px rgba(255,107,53,0.1); }
  .card-pita { background: linear-gradient(135deg, rgba(46,204,113,0.15) 0%, rgba(46,204,113,0.04) 100%); border: 2px solid #2ECC71; }
  .card-regular { background-color: #131B2E; border: 1px solid #232D42; }
  
  /* Componentes Internos */
  .teams-line { display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 6px; min-width: 0; }
  .team-name { flex: 1; font-size: 13px; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #FFFFFF; }
  .team-left { text-align: right; }
  .team-right { text-align: left; }
  .vs-badge { font-size: 9px; font-weight: 900; padding: 2px 5px; border-radius: 4px; flex-shrink: 0; letter-spacing: 0.5px; }
  .vs-juega { background-color: #FF6B35; color: #0B0F19; }
  .vs-regular { background-color: #232D42; color: #94A3B8; }
  .ref-line { margin-top: 8px; text-align: center; font-size: 11px; color: #64748B; font-weight: 600; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ref-active { color: #2ECC71; font-weight: 800; }
  
  /* 📱 RESPONSIVO MÓVIL DIRECTO */
  @media (max-width: 550px) {
    .cancha-headers { display: none; }
    .match-row { flex-direction: column; align-items: stretch; gap: 4px; background-color: rgba(19, 27, 46, 0.3); padding: 10px; border-radius: 14px; border: 1px solid rgba(35, 45, 66, 0.4); }
    .time-block { width: 100%; padding: 2px 0 6px 4px; background: transparent; border: none; text-align: left; font-size: 14px; }
    .cards-wrapper { flex-direction: column; gap: 8px; width: 100%; }
    .cancha-badge { display: inline-block; font-size: 9px; font-weight: 800; text-transform: uppercase; background-color: rgba(74, 144, 226, 0.15); color: #4A90E2; padding: 2px 6px; border-radius: 4px; margin-bottom: 6px; width: fit-content; }
    .team-name { font-size: 12px; }
  }
</style>
"""

# ==========================================
# HEADER ADAPTABLE A TEMAS (LIGHT / DARK)
# ==========================================
HEADER_HTML = f'<div style="text-align: center; margin-bottom: 24px; font-family: system-ui, -apple-system, sans-serif;"><div style="display: inline-flex; align-items: center; background: #1E293B; padding: 6px 18px; border-radius: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #334155; margin-bottom: 12px;">{BALON_WEB_IMG}<span style="color: #F8FAFC; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;">TORNEO OFICIAL 2026</span></div><h1 style="color: var(--text-color, #0F172A); font-size: 42px; font-weight: 900; letter-spacing: -1.5px; margin: 0; text-transform: uppercase; line-height: 0.95;">LIGA LA CHONA</h1><div style="width: 60px; height: 4px; background: linear-gradient(90deg, #FF6B35, #D44A1D); margin: 14px auto 0 auto; border-radius: 2px;"></div></div>'

st.markdown(HEADER_HTML, unsafe_allow_html=True)

# ==========================================
# FILTROS DE INTERFAZ
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
# LÓGICA DE MAQUETACIÓN RESPONSIVA
# ==========================================
def obtener_html_tarjeta(partido, eq_filtro, cancha_label):
    if not partido:
        return f"""
        <div class="card-closed">
            <div style="display: flex; flex-direction: column; width: 100%;">
                <span class="cancha-badge">{cancha_label}</span>
                <span style="text-align: center; width: 100%;">🌙 Cerrado</span>
            </div>
        </div>"""
    
    loc, vis = equipos_map.get(partido["equipo_local_id"]), equipos_map.get(partido["equipo_visita_id"])
    arb = equipos_map.get(partido["equipo_arbitro_id"], "Sin Árbitro")
    juega = (loc == eq_filtro or vis == eq_filtro) and eq_filtro != "VER TODO"
    pita = (arb == eq_filtro) and eq_filtro != "VER TODO"
    
    if juega:
        clase_card, clase_vs = "card-juega", "vs-juega"
    elif pita:
        clase_card, clase_vs = "card-pita", "vs-regular"
    else:
        clase_card, clase_vs = "card-regular", "vs-regular"
        
    if pita:
        html_arb = f'<span class="ref-active">{WHISTLE_SVG} PITA: {arb.upper()}</span>'
    else:
        html_arb = f'{WHISTLE_SVG} Pita: <span style="color: #94A3B8;">{arb}</span>'
        
    lagos_icon = CAR_SVG if "lagos" in vis.lower() else ""

    return f"""
    <div class="match-card {clase_card}">
        <span class="cancha-badge">{cancha_label}</span>
        <div class="teams-line">
            <div class="team-name team-left">{loc}</div>
            <div class="vs-badge {clase_vs}">VS</div>
            <div class="team-name team-right">{vis}{lagos_icon}</div>
        </div>
        <div class="ref-line">{html_arb}</div>
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
        <div class="match-row">
            <div class="time-block">🕒 {h.replace(' PM', '')}</div>
            <div class="cards-wrapper">
                {obtener_html_tarjeta(p_c1, equipo_val, "Cancha 1")}
                {obtener_html_tarjeta(p_c2, equipo_val, "Cancha 2")}
            </div>
        </div>"""
        
    return f"""
    <div class="jornada-container">
        <div class="jornada-header">
            <div class="jornada-title">JORNADA {j_num}</div>
            <div class="jornada-status">{estatus}</div>
        </div>
        <div class="cancha-headers">
            <div class="cancha-header-space"></div>
            <div class="cancha-title">Cancha 1</div>
            <div class="cancha-title">Cancha 2</div>
        </div>
        <div class="rows-container">{bloques}</div>
    </div>"""

# ==========================================
# INYECCIÓN Y AJUSTE DE LIENZO IFRAME
# ==========================================
pizarra = f'<div class="pizarra-body">{CSS_HOJA_ESTILOS}'
if jornada_val == "TODAS":
    for j in jornadas: pizarra += generar_html_jornada(j)
    h_c = 2800
else:
    pizarra += generar_html_jornada(jornada_val)
    h_c = 540
pizarra += '</div>'

components.html(pizarra, height=h_c, scrolling=True)