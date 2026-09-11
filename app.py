import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
from html import escape
from itertools import combinations

# Configuración inicial de la página móvil/web
st.set_page_config(
    page_title="Liga La Chona",
    page_icon="🏐",
    layout="wide"
)

# ==========================================
# 🚨 CONTROL DE MANTENIMIENTO (DESACTIVADO)
# ==========================================
MODO_PAUSA = st.secrets.get("MODO_PAUSA", False)

if MODO_PAUSA:
    st.warning("⚠️ **La Chona Liga está en mantenimiento temporal.**")
    st.info("Estamos actualizando la base de datos y los roles de juego de la semana. ¡Regresamos en breve! 🏐")
    st.stop()

# ==========================================
# 🎛️ CONTROL DE JORNADA ACTIVA Y FECHAS AUTOMÁTICO
# ==========================================
FECHA_BASE_TORNEO = datetime(2026, 5, 23)

# CÁLCULO AUTOMÁTICO
fecha_pivote = datetime.now() + timedelta(days=5)
JORNADA_ACTIVA = max(1, ((fecha_pivote - FECHA_BASE_TORNEO).days // 7) + 1)

def obtener_fecha_sabado(numero_jornada):
    semanas_a_sumar = int(numero_jornada) - 1
    fecha_calculada = FECHA_BASE_TORNEO + timedelta(weeks=semanas_a_sumar)
    meses_espanol = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    return f"{fecha_calculada.day} {meses_espanol[fecha_calculada.month]}"

def obtener_fecha_iso(numero_jornada):
    semanas_a_sumar = int(numero_jornada) - 1
    fecha_calculada = FECHA_BASE_TORNEO + timedelta(weeks=semanas_a_sumar)
    return fecha_calculada.strftime("%Y-%m-%d")

# ==========================================
# 🛑 BLINDAJE DE INTERFAZ
# ==========================================
st.markdown("""
    <style>
        [data-testid="stHeader"], 
        header, 
        footer, 
        .stDeployButton, 
        #MainMenu, 
        [data-testid="stToolbar"] { 
            visibility: hidden !important; 
            display: none !important; 
        }
        .block-container {
            padding-top: 1rem !important;
            max-width: 96% !important;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

@st.cache_data(ttl=60)
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

# Hoja de estilos centralizada para la pizarra HTML
CSS_HOJA_ESTILOS = """
<style>
  .pizarra-body { margin: 0; padding: 2px; font-family: system-ui, -apple-system, sans-serif; background-color: transparent; }
  .jornada-container { background-color: #060B14; padding: 16px; border-radius: 16px; margin-bottom: 24px; border: 1px solid #131B2E; box-shadow: 0 10px 30px rgba(0,0,0,0.35); width: 100%; box-sizing: border-box; }
  .jornada-header { text-align: center; border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 14px; }
  .jornada-title { font-size: 19px; font-weight: 900; color: #FF6B35; text-transform: uppercase; letter-spacing: 0.5px; }
  .jornada-status { font-size: 11px; color: #38BDF8; font-weight: 700; margin-top: 5px; letter-spacing: 0.5px; }
  .cancha-headers { display: flex; gap: 12px; margin-bottom: 10px; text-align: center; opacity: 0.9; }
  .cancha-header-space { width: 70px; flex-shrink: 0; }
  .cancha-title { flex: 1; color: #4A90E2; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
  .rows-container { display: flex; flex-direction: column; gap: 12px; }
  .match-row { display: flex; align-items: center; gap: 12px; width: 100%; }
  .time-block { width: 70px; background-color: #131B2E; border: 1px solid #232D42; text-align: center; padding: 10px 0; border-radius: 10px; font-weight: 800; font-size: 12px; color: #FF6B35; flex-shrink: 0; }
  .cards-wrapper { display: flex; gap: 12px; flex: 1; min-width: 0; }
  
  /* ESTILOS DE LA TARJETA (Añadido position: relative para la etiqueta V2) */
  .match-card { position: relative; flex: 1; border-radius: 12px; padding: 14px 12px; display: flex; flex-direction: column; justify-content: space-between; min-height: 76px; box-sizing: border-box; min-width: 0; }
  .cancha-badge { display: none; }
  
  .card-closed { flex: 1; min-width: 0; background-color: #0B0F19; border: 1px dashed #232D42; border-radius: 12px; display: flex; justify-content: center; align-items: center; color: #475569; font-size: 12px; font-style: italic; min-height: 76px; box-sizing: border-box; }
  .card-juega { background: linear-gradient(135deg, rgba(255,107,53,0.18) 0%, rgba(212,74,29,0.06) 100%); border: 2px solid #FF6B35; box-shadow: 0 0 15px rgba(255,107,53,0.1); }
  .card-pita { background: linear-gradient(135deg, rgba(46,204,113,0.15) 0%, rgba(46,204,113,0.04) 100%); border: 2px solid #2ECC71; }
  .card-regular { background-color: #131B2E; border: 1px solid #232D42; }
  
  .teams-line { display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 6px; min-width: 0; }
  .team-name { flex: 1; font-size: 13px; font-weight: 800; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #FFFFFF; }
  .team-left { text-align: right; }
  .team-right { text-align: left; }
  .vs-badge { font-size: 9px; font-weight: 900; padding: 2px 5px; border-radius: 4px; flex-shrink: 0; letter-spacing: 0.5px; }
  .vs-juega { background-color: #FF6B35; color: #0B0F19; }
  .vs-regular { background-color: #232D42; color: #94A3B8; }
  .ref-line { margin-top: 8px; text-align: center; font-size: 11px; color: #64748B; font-weight: 600; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ref-active { color: #2ECC71; font-weight: 800; }

  /* 🏷️ ESTILOS DEL BADGE DE VUELTA */
  .vuelta-badge { position: absolute; bottom: 8px; right: 10px; font-size: 9px; font-weight: 900; padding: 2px 6px; border-radius: 4px; letter-spacing: 0.5px; z-index: 2; }
  .v2-badge { background-color: rgba(255, 107, 53, 0.15); color: #FF6B35; border: 1px dashed rgba(255, 107, 53, 0.4); }
  
  .jornada-preliminar { border: 1px dashed #EAB308 !important; box-shadow: 0 10px 30px rgba(234, 179, 8, 0.03) !important; }
  .status-preliminar { color: #EAB308 !important; font-weight: 800 !important; }

  /* MATRIZ */
  .matrix-wrapper { width: 100%; overflow-x: auto; border-radius: 16px; border: 1px solid #131B2E; box-shadow: 0 10px 30px rgba(0,0,0,0.35); margin-top: 10px; }
  .matrix-table { width: 100%; border-collapse: collapse; background-color: #060B14; font-size: 12px; text-align: center; }
  .matrix-table th, .matrix-table td { padding: 14px 12px; border: 1px solid #131B2E; white-space: nowrap; }
  .matrix-table th { background-color: #131B2E; color: #94A3B8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
  .matrix-team-header { background-color: #131B2E !important; color: #FFFFFF; font-weight: 800; text-align: left; position: sticky; left: 0; font-size: 13px; }
  .cell-diagonal { background-color: rgba(255, 107, 53, 0.12) !important; color: #FF6B35; font-weight: bold; }
  .cell-ganado { background-color: rgba(46, 204, 113, 0.16) !important; color: #2ECC71; font-weight: 800; text-transform: uppercase; }
  .cell-perdido { background-color: rgba(231, 76, 60, 0.16) !important; color: #E74C3C; font-weight: 800; text-transform: uppercase; }
  .cell-vacia { color: #475569; font-style: italic; font-size: 14px; }
  .section-card { background-color: #060B14; border: 1px solid #131B2E; border-radius: 16px; padding: 18px; margin: 14px 0 26px; box-shadow: 0 10px 30px rgba(0,0,0,0.25); }
  .section-title { color: #FFFFFF; text-align: center; font-size: 19px; font-weight: 900; margin: 0 0 4px; }
  .section-help { color: #94A3B8; text-align: center; font-size: 12px; margin: 0 0 16px; }
  .ranking-wrapper { width: 100%; overflow-x: auto; border-radius: 12px; border: 1px solid #1E293B; }
  .ranking-table { width: 100%; min-width: 560px; border-collapse: collapse; background-color: #060B14; font-size: 13px; }
  .ranking-table th, .ranking-table td { padding: 12px 10px; border-bottom: 1px solid #131B2E; text-align: center; }
  .ranking-table th { background-color: #131B2E; color: #94A3B8; font-size: 11px; text-transform: uppercase; letter-spacing: .5px; }
  .ranking-table td { color: #E2E8F0; }
  .ranking-table .rank-position { color: #FF6B35; font-weight: 900; font-size: 15px; }
  .ranking-table .rank-team { text-align: left; color: #FFFFFF; font-weight: 800; position: sticky; left: 0; background-color: #060B14; }
  .ranking-table .rank-wins { color: #2ECC71; font-weight: 900; }
  .ranking-table .rank-losses { color: #E74C3C; font-weight: 800; }
  .matrix-table { min-width: 760px; }
  .matrix-table th { position: sticky; top: 0; z-index: 2; }
  .matrix-team-header { z-index: 3; }
  .matrix-legend { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin-top: 12px; color: #94A3B8; font-size: 11px; }
  .legend-chip { padding: 4px 8px; border-radius: 999px; border: 1px solid #1E293B; }
  .section-card { font-family: system-ui, sans-serif; }
  .mobile-matches, .mobile-full-matrix { display: none; }
  .team-details, .full-matrix { color: #E2E8F0; border: 1px solid #334155; border-radius: 10px; margin: 8px 0; }
  .team-details summary, .full-matrix summary { padding: 14px 12px; min-height: 44px; box-sizing: border-box; cursor: pointer; font-weight: 700; }
  .team-details summary:focus-visible, .full-matrix summary:focus-visible { outline: 2px solid #38BDF8; }
  .rival-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: center; padding: 12px; border-top: 1px solid #334155; font-size: 13px; overflow-wrap: anywhere; }
  .estado { display: inline-block; font-size: 11px; padding: 4px 6px; border-radius: 5px; margin: 2px 0; }
  .ganado { color: #86EFAC; background: #143826; }
  .perdido { color: #FCA5A5; background: #451D25; }
  .programado { color: #FDE68A; background: #423718; }
  .sin-programar { color: #CBD5E1; }
  .matrix-wrapper { max-height: 65vh; overflow: auto; }
  .matrix-table { border-collapse: separate; border-spacing: 0; }
  .matrix-table .matrix-team-header { top: auto; z-index: 1; white-space: normal; min-width: 120px; max-width: 180px; }
  .full-matrix > .section-help { padding: 12px; text-align: left; line-height: 1.8; }

  @media (max-width: 550px) {
    .cancha-headers { display: none; }
    .match-row { flex-direction: column; align-items: stretch; gap: 4px; background-color: rgba(19, 27, 46, 0.3); padding: 10px; border-radius: 14px; border: 1px solid rgba(35, 45, 66, 0.4); }
    .time-block { width: 100%; padding: 2px 0 6px 4px; background: transparent; border: none; text-align: left; font-size: 14px; }
    .cards-wrapper { flex-direction: column; gap: 8px; width: 100%; }
    .cancha-badge { display: inline-block; font-size: 9px; font-weight: 800; text-transform: uppercase; background-color: rgba(74, 144, 226, 0.15); color: #4A90E2; padding: 2px 6px; border-radius: 4px; margin-bottom: 6px; width: fit-content; }
    .team-name { font-size: 12px; }
    .section-card { padding: 12px 8px; border-radius: 12px; }
    .matrix-table th, .matrix-table td { padding: 10px 8px; font-size: 11px; }
    .matrix-team-header { max-width: 132px; overflow: hidden; text-overflow: ellipsis; }
    .mobile-matches { display: block; }
    .mobile-full-matrix { display: block; }
    .desktop-matrix { display: none; }
    .ranking-table { min-width: 0; table-layout: fixed; font-size: 11px; }
    .ranking-table th, .ranking-table td { padding: 10px 3px; overflow-wrap: anywhere; }
    .ranking-table th:nth-child(2), .ranking-table td:nth-child(2) { width: 34%; }
    .ranking-table .rank-team { position: static; }
    .section-title { font-size: 17px; }
    .match-row { box-sizing: border-box; }
  }
</style>
"""

HEADER_HTML = f"""
<div style="text-align: center; margin-bottom: 24px; font-family: system-ui, -apple-system, sans-serif;">
    <div style="display: inline-flex; align-items: center; background: #1E293B; padding: 6px 18px; border-radius: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #334155; margin-bottom: 12px;">
        {BALON_WEB_IMG}
        <span style="color: #F8FAFC; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;">TORNEO OFICIAL 2026</span>
    </div>
    <h1 style="color: #FFFFFF; font-size: 42px; font-weight: 900; letter-spacing: -1.5px; margin: 0; text-transform: uppercase; line-height: 0.95;">LIGA LA CHONA</h1>
    <div style="width: 60px; height: 4px; background: linear-gradient(90deg, #FF6B35, #D44A1D); margin: 14px auto 0 auto; border-radius: 2px;"></div>
</div>
"""

# ==========================================
# 🎫 SEPARACIÓN DE PESTAÑAS
# ==========================================
tab_publico, tab_resumen, tab_clasificacion = st.tabs(["🏐 ROL", "📈 RESUMEN", "🏆 CLASIFICACIÓN"])

# ==========================================
# 👥 PESTAÑA 1: VISTA PÚBLICA
# ==========================================
with tab_publico:
    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        jornadas_db = list(set([p["jornada"] for p in partidos_data]))
        if JORNADA_ACTIVA not in jornadas_db:
            jornadas_db.append(JORNADA_ACTIVA)
        jornadas = sorted(jornadas_db)
        
        opciones_j = ["📅 TODAS LAS JORNADAS"] + [f"📅 JORNADA {j}" for j in jornadas]
        string_jornada_activa = f"📅 JORNADA {JORNADA_ACTIVA}"
        default_index = opciones_j.index(string_jornada_activa) if string_jornada_activa in opciones_j else 1
        
        jornada_sel = st.selectbox("Jornada", opciones_j, index=default_index, filter_mode=None)
        jornada_val = "TODAS" if "TODAS" in jornada_sel else int(jornada_sel.split("JORNADA ")[1])

    with col2:
        opciones_e = ["🔍 TODOS LOS EQUIPOS"] + sorted(list(equipos_map.values()))
        equipo_sel = st.selectbox("Equipo", opciones_e, index=0, filter_mode=None)
        equipo_val = "VER TODO" if "TODOS" in equipo_sel else equipo_sel

    def obtener_html_tarjeta(partido, eq_filtro, cancha_label):
        if not partido:
            return f"""
            <div class="card-closed">
                <div style="display: flex; flex-direction: column; width: 100%;">
                    <span class="cancha-badge">{cancha_label}</span>
                    <span style="text-align: center; width: 100%;">🌙 Cerrado</span>
                </div>
            </div>"""
        
        loc = equipos_map.get(partido["equipo_local_id"])
        vis = equipos_map.get(partido["equipo_visita_id"])
        arb = equipos_map.get(partido["equipo_arbitro_id"], "Sin Árbitro")
        
        # Extracción y diseño de la VUELTA
        vuelta_num = partido.get("vuelta", 1)
        if vuelta_num is None: vuelta_num = 1
        
        html_vuelta = ""
        if int(vuelta_num) >= 2:
            html_vuelta = f'<div class="vuelta-badge v2-badge">V{int(vuelta_num)}</div>'
        
        juega = (loc == eq_filtro or vis == eq_filtro) and eq_filtro != "VER TODO"
        pita = (arb == eq_filtro) and eq_filtro != "VER TODO"
        
        clase_card = "card-juega" if juega else ("card-pita" if pita else "card-regular")
        clase_vs = "vs-juega" if juega else "vs-regular"
        
        html_arb = f'<span class="ref-active">{WHISTLE_SVG} PITA: {arb.upper()}</span>' if (arb == eq_filtro and eq_filtro != "VER TODO") else f'{WHISTLE_SVG} Pita: <span style="color: #94A3B8;">{arb}</span>'
        lagos_icon = CAR_SVG if "lagos" in vis.lower() else ""

        if partido.get("ganador_id") is not None:
            if partido["ganador_id"] == partido["equipo_local_id"]:
                loc = f"👑 <span style='color: #FF6B35; font-weight:900;'>{loc}</span>"
                vis = f"<span style='opacity: 0.35; font-weight:500;'>{vis}</span>"
            elif partido["ganador_id"] == partido["equipo_visita_id"]:
                loc = f"<span style='opacity: 0.35; font-weight:500;'>{loc}</span>"
                vis = f"👑 <span style='color: #FF6B35; font-weight:900;'>{vis}</span>{lagos_icon}"

        return f"""
        <div class="match-card {clase_card}">
            {html_vuelta}
            <span class="cancha-badge">{cancha_label}</span>
            <div class="teams-line">
                <div class="team-name team-left">{loc}</div>
                <div class="vs-badge {clase_vs}">VS</div>
                <div class="team-name team-right">{vis}</div>
            </div>
            <div class="ref-line">{html_arb}</div>
        </div>
        """

    def generar_html_jornada(j_num):
        partidos = [p for p in partidos_data if p["jornada"] == int(j_num)]
        fecha_correspondiente = obtener_fecha_sabado(j_num)
        
        if not partidos:
            return f"""
            <div class="jornada-container jornada-preliminar" style="text-align: center; padding: 35px 20px;">
                <div class="jornada-header" style="border:none; padding:0; margin:0;">
                    <div class="jornada-title">JORNADA {j_num} — {fecha_correspondiente.upper()}</div>
                    <div class="jornada-status status-preliminar" style="font-size: 13px; margin-top: 14px; letter-spacing:1px;">⏳ EN ESPERA DE CONFIRMACIÓN</div>
                </div>
                <p style="color: #64748B; font-size: 12px; margin-top: 12px; font-style: italic;">Los delegados están confirmando asistencia.</p>
            </div>"""

        tiene_lagos = any("lagos" in equipos_map.get(p["equipo_visita_id"], "").lower() for p in partidos)
        
        if int(j_num) > JORNADA_ACTIVA:
            estatus = "⏳ ROL PRELIMINAR: Sujeto a modificaciones"
            clase_contenedor, clase_status = "jornada-container jornada-preliminar", "jornada-status status-preliminar"
        else:
            estatus = "⚡ JORNADA ESPECIAL: Lagos de visita" if tiene_lagos else "🏠 OPERACIÓN REGULAR"
            clase_contenedor, clase_status = "jornada-container", "jornada-status"
        
        bloques = ""
        for h in ["7:00 PM", "8:00 PM", "9:00 PM"]:
            p_hora = [p for p in partidos if p["hora"] == h]
            p_c1 = next((p for p in p_hora if p["cancha"] == "Cancha 1"), None)
            p_c2 = next((p for p in p_hora if p["cancha"] == "Cancha 2"), None)
            if h == "7:00 PM" and not p_c1 and not p_c2: continue
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
        <div class="{clase_contenedor}">
            <div class="jornada-header">
                <div class="jornada-title">JORNADA {j_num} — {fecha_correspondiente.upper()}</div>
                <div class="{clase_status}">{estatus}</div>
            </div>
            <div class="cancha-headers">
                <div class="cancha-header-space"></div>
                <div class="cancha-title">Cancha 1</div>
                <div class="cancha-title">Cancha 2</div>
                </div>
            <div class="rows-container">{bloques}</div>
        </div>"""

    pizarra = f'<div class="pizarra-body">{CSS_HOJA_ESTILOS}'
    if jornada_val == "TODAS":
        for j in jornadas: pizarra += generar_html_jornada(j)
        h_c = 2800
    else:
        pizarra += generar_html_jornada(jornada_val)
        partidos_existentes = [p for p in partidos_data if p["jornada"] == jornada_val]
        h_c = 540 if partidos_existentes else 240
    pizarra += '</div>'

    components.html(pizarra, height=h_c, scrolling=True)


# ==========================================
# 🏆 PESTAÑA 2: CLASIFICACIÓN Y MATRICES
# ==========================================
def vuelta_de(partido):
    try:
        return int(partido.get("vuelta") or 1)
    except (TypeError, ValueError):
        return None


def resultado_valido(partido):
    local = partido.get("equipo_local_id")
    visita = partido.get("equipo_visita_id")
    return (local in equipos_map and visita in equipos_map and local != visita
            and partido.get("ganador_id") in (local, visita))


with tab_resumen:
    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    st.subheader("Avance del torneo")
    # Exclusión visual del resumen; el catálogo y las otras pantallas se conservan.
    excluidos_resumen = {"lagos", "sub17", "independientes"}
    equipos_resumen = {
        i: nombre for i, nombre in equipos_map.items()
        if "".join(c for c in nombre.casefold() if c.isalnum()) not in excluidos_resumen
    }
    partidos_resumen = [p for p in partidos_data
                        if p.get("equipo_local_id") in equipos_resumen
                        and p.get("equipo_visita_id") in equipos_resumen]
    jugados = [p for p in partidos_resumen if resultado_valido(p)]
    segunda = [p for p in partidos_resumen if vuelta_de(p) == 2]
    jugados_segunda = [p for p in segunda if resultado_valido(p)]
    # Cada pareja cuenta una vez, independientemente de local/visita o repeticiones.
    cruces_totales = {frozenset(par) for par in combinations(equipos_resumen, 2)}
    cruces_jugados = {frozenset((p["equipo_local_id"], p["equipo_visita_id"])) for p in jugados_segunda}
    cruces_pendientes = cruces_totales - cruces_jugados
    pendientes_segunda = []
    for local, visita in combinations(sorted(equipos_resumen, key=lambda i: equipos_resumen[i].casefold()), 2):
        cruce = frozenset((local, visita))
        if cruce not in cruces_pendientes:
            continue
        programados = [p for p in segunda if frozenset((p.get("equipo_local_id"), p.get("equipo_visita_id"))) == cruce]
        pendientes_segunda.append(programados[0] if programados else {
            "equipo_local_id": local, "equipo_visita_id": visita,
        })
    for columna, etiqueta, cantidad in zip(
        st.columns(3),
        ["Jugados · torneo", "Jugados · Vuelta 2", "Pendientes · Vuelta 2"],
        [len(jugados), len(jugados_segunda), len(cruces_pendientes)],
    ):
        columna.metric(etiqueta, cantidad)
    st.caption(f"Todos contra todos entre los {len(equipos_resumen)} equipos incluidos en este resumen: un cruce por pareja. Los conteos excluyen a Lagos, Sub 17 e Independientes. Los pendientes incluyen los que aún no tienen fecha; las repeticiones no reducen otros cruces pendientes.")
    if cruces_totales:
        st.progress(len(cruces_jugados) / len(cruces_totales),
                    text=f"{len(cruces_jugados)} de {len(cruces_totales)} cruces de Vuelta 2 completados")
    else:
        st.info("Se necesitan al menos dos equipos para calcular los cruces.")
    st.subheader("Rivales pendientes · Vuelta 2")
    st.caption("Selecciona un equipo para ver contra quién le falta jugar.")
    equipos_ordenados = sorted(equipos_resumen, key=lambda i: equipos_resumen[i].casefold())
    pendientes_por_equipo = {
        equipo: [rival for rival in equipos_ordenados
                 if rival != equipo and frozenset((equipo, rival)) in cruces_pendientes]
        for equipo in equipos_ordenados
    }
    if equipos_ordenados:
        lista_equipos, lista_rivales = st.columns([1, 1.5], gap="large")
        with lista_equipos:
            seleccionado = st.radio(
                "Todos los equipos",
                equipos_ordenados,
                format_func=lambda i: f"{equipos_map[i]} · {len(pendientes_por_equipo[i])} pendientes",
                key="equipo_resumen_v2_filtrado",
            )
        with lista_rivales:
            st.text(equipos_map[seleccionado])
            rivales = pendientes_por_equipo[seleccionado]
            st.caption(f"{len(rivales)} rivales pendientes en la segunda vuelta")
            if not rivales:
                st.success("¡Ya completó todos sus cruces de la Vuelta 2!")
            for rival in rivales:
                cruce = frozenset((seleccionado, rival))
                programados = [p for p in segunda
                               if frozenset((p.get("equipo_local_id"), p.get("equipo_visita_id"))) == cruce]
                with st.container(border=True):
                    st.text(equipos_map[rival])
                    if not programados:
                        st.caption("Por programar · todavía sin fecha")
                    for p in programados:
                        estado = "Programado" if p.get("ganador_id") is None else "Resultado por revisar"
                        st.caption(f"{estado} · Jornada {p.get('jornada', '—')} · {p.get('fecha') or 'Sin fecha'} · {p.get('hora') or 'Sin hora'} · {p.get('cancha') or 'Sin cancha'}")
    else:
        st.info("Todavía no hay equipos registrados.")


with tab_clasificacion:
    st.markdown(HEADER_HTML, unsafe_allow_html=True)

    def generar_html_ranking():
        estadisticas = {
            equipo_id: {"nombre": nombre, "jugados": 0, "ganados": 0, "perdidos": 0}
            for equipo_id, nombre in equipos_map.items()
        }

        for partido in partidos_data:
            ganador_id = partido.get("ganador_id")
            if not resultado_valido(partido):
                continue

            local_id = partido.get("equipo_local_id")
            visita_id = partido.get("equipo_visita_id")
            perdedor_id = visita_id if ganador_id == local_id else local_id

            if ganador_id in estadisticas and perdedor_id in estadisticas:
                for equipo_id in (ganador_id, perdedor_id):
                    estadisticas[equipo_id]["jugados"] += 1
                estadisticas[ganador_id]["ganados"] += 1
                estadisticas[perdedor_id]["perdidos"] += 1

        ranking = sorted(
            estadisticas.values(),
            key=lambda item: (-item["ganados"], item["perdidos"], item["nombre"].casefold())
        )

        filas = ""
        for posicion, equipo in enumerate(ranking, start=1):
            efectividad = (equipo["ganados"] / equipo["jugados"] * 100) if equipo["jugados"] else 0
            filas += f"""
            <tr>
                <td class="rank-position">{posicion}</td>
                <td class="rank-team">{escape(equipo['nombre'])}</td>
                <td>{equipo['jugados']}</td>
                <td class="rank-wins">{equipo['ganados']}</td>
                <td class="rank-losses">{equipo['perdidos']}</td>
                <td>{efectividad:.0f}%</td>
            </tr>"""

        return f"""
        <div class="section-card">
            <h2 class="section-title">🏆 CLASIFICACIÓN GENERAL</h2>
            <p class="section-help">Solo se contabilizan partidos con resultado oficial.</p>
            <div class="ranking-wrapper">
                <table class="ranking-table">
                    <thead><tr><th>Pos.</th><th style="text-align:left;">Equipo</th><th>PJ</th><th>PG</th><th>PP</th><th>Efect.</th></tr></thead>
                    <tbody>{filas}</tbody>
                </table>
            </div>
        </div>"""

    def generar_html_matriz_resultados(vuelta):
        ids = sorted(equipos_map, key=lambda i: equipos_map[i].casefold())
        historial = {i: {j: [] for j in ids if j != i} for i in ids}
        for p in partidos_data:
            if vuelta_de(p) != vuelta:
                continue
            local, visita = p.get("equipo_local_id"), p.get("equipo_visita_id")
            if local not in historial or visita not in historial[local]:
                continue
            for equipo, rival in ((local, visita), (visita, local)):
                if resultado_valido(p):
                    estado = "Ganó" if p["ganador_id"] == equipo else "Perdió"
                else:
                    estado = "Programado" if p.get("ganador_id") is None else "Revisar resultado"
                historial[equipo][rival].append((estado, p.get("jornada")))

        def celda(equipo, rival):
            registros = historial[equipo][rival]
            if not registros:
                return '<span class="estado sin-programar">Sin programar</span>'
            etiquetas = []
            for estado, jornada in registros:
                clase = {"Ganó": "ganado", "Perdió": "perdido", "Programado": "programado"}.get(estado, "programado")
                etiquetas.append(f'<span class="estado {clase}">{estado} · J{escape(str(jornada or "—"))}</span>')
            return "<br>".join(etiquetas)

        tabla = '<div class="matrix-wrapper" role="region" aria-label="Matriz de enfrentamientos" tabindex="0"><table class="matrix-table"><thead><tr><th>Equipo</th>'
        for numero, equipo in enumerate(ids, 1):
            tabla += f'<th scope="col" title="{escape(equipos_map[equipo])}">{numero}</th>'
        tabla += '</tr></thead><tbody>'
        movil = '<div class="mobile-matches">'
        for numero, equipo in enumerate(ids, 1):
            nombre = escape(equipos_map[equipo])
            tabla += f'<tr><th scope="row" class="matrix-team-header">{numero}. {nombre}</th>'
            movil += f'<details class="team-details"><summary>{nombre}</summary>'
            for rival in ids:
                if rival == equipo:
                    tabla += '<td class="cell-diagonal">—</td>'
                    continue
                contenido = celda(equipo, rival)
                tabla += f'<td>{contenido}</td>'
                movil += f'<div class="rival-row"><span>{escape(equipos_map[rival])}</span><div>{contenido}</div></div>'
            tabla += '</tr>'
            movil += '</details>'
        tabla += '</tbody></table></div>'
        movil += '</div>'
        clave = " · ".join(f"{n}. {escape(equipos_map[i])}" for n, i in enumerate(ids, 1))
        return f"""<div class="section-card">
            <h2 class="section-title">Matriz · Vuelta {vuelta}</h2>
            <p class="section-help">El resultado se lee desde el equipo de la fila. Cada registro muestra su jornada.</p>
            {movil}
            <div class="desktop-matrix">{tabla}<p class="section-help">{clave}</p></div>
            <details class="full-matrix mobile-full-matrix"><summary>Ver tabla completa · desliza horizontalmente</summary>{tabla}
            <p class="section-help">{clave}</p></details>
        </div>"""

    # HTML directo para usar el desplazamiento normal de la página.
    st.html(CSS_HOJA_ESTILOS)
    st.html(generar_html_ranking())
    st.html(generar_html_matriz_resultados(1))
    st.html(generar_html_matriz_resultados(2))
