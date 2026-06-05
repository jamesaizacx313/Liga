import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta

# Configuración inicial de la página móvil/web
st.set_page_config(
    page_icon="https://img.icons8.com/color/96/volleyball.png",
    layout="centered"
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
# 🎛️ CONTROL DE JORNADA ACTIVA Y FECHAS
# ==========================================
JORNADA_ACTIVA = 3  # Apunta de forma nativa a la jornada de este próximo sábado

# Fecha de inicio del torneo: Jornada 1 = Sábado 23 de Mayo de 2026
FECHA_BASE_TORNEO = datetime(2026, 5, 23)

def obtener_fecha_sabado(numero_jornada):
    """Calcula dinámicamente la fecha del sábado correspondiente a la jornada."""
    semanas_a_sumar = int(numero_jornada) - 1
    fecha_calculada = FECHA_BASE_TORNEO + timedelta(weeks=semanas_a_sumar)
    
    meses_espanol = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    dia = fecha_calculada.day
    mes = meses_espanol[fecha_calculada.month]
    return f"{dia} {mes}"

# ==========================================
# 🛑 BLINDAJE DE INTERFAZ: OCULTAR TODO LO NATIVO
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
        }
    </style>
""", unsafe_allow_html=True)

# Conexión segura a Supabase usando los Secrets de Streamlit
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Descarga de datos optimizada con caché automática de 5 minutos (TTL = 300s)
@st.cache_data(ttl=300)
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
# 📌 ASSETS GRÁFICOS VECTORIALES (SVG INLINE)
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
  .match-card { flex: 1; border-radius: 12px; padding: 14px 12px; display: flex; flex-direction: column; justify-content: space-between; min-height: 76px; box-sizing: border-box; min-width: 0; }
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
  
  .jornada-preliminar { border: 1px dashed #EAB308 !important; box-shadow: 0 10px 30px rgba(234, 179, 8, 0.03) !important; }
  .status-preliminar { color: #EAB308 !important; font-weight: 800 !important; }

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
tab_publico, tab_admin = st.tabs(["🏐 ROL Y RESULTADOS", "🔒 GENERADOR DE ROL"])

# ==========================================
# 👥 PESTAÑA 1: VISTA PÚBLICA DE JUGADORES
# ==========================================
with tab_publico:
    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        jornadas_db = list(set([p["jornada"] for p in partidos_data]))
        if 3 not in jornadas_db:
            jornadas_db.append(3)
        jornadas = sorted(jornadas_db)
        
        opciones_j = ["📅 TODAS LAS JORNADAS"] + [f"📅 JORNADA {j}" for j in jornadas]
        default_index = opciones_j.index("📅 JORNADA 3") if "📅 JORNADA 3" in opciones_j else 1
        
        jornada_sel = st.selectbox("j_f", opciones_j, index=default_index, label_visibility="collapsed")
        jornada_val = "TODAS" if "TODAS" in jornada_sel else int(jornada_sel.split("JORNADA ")[1])

    with col2:
        opciones_e = ["🔍 TODOS LOS EQUIPOS"] + sorted(list(equipos_map.values()))
        equipo_sel = st.selectbox("e_f", opciones_e, index=0, label_visibility="collapsed")
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
                <p style="color: #64748B; font-size: 12px; margin-top: 10px; font-style: italic;">Los delegados están confirmando asistencia y horarios disponibles para las canchas.</p>
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
        h_c = 540 if partidos_existentes else 200
    pizarra += '</div>'

    components.html(pizarra, height=h_c, scrolling=True)


# ==========================================
# 🔒 PESTAÑA 2: MÓDULO ADMINISTRADOR SEGURO
# ==========================================
with tab_admin:
    st.markdown("### ⚙️ Panel de Control Operacional")
    
    password_admin = st.text_input("Introduce la clave de acceso de la liga:", type="password")
    
    try:
        clave_correcta = st.secrets["ADMIN_PASSWORD"]
        
        if password_admin == clave_correcta:
            st.success("🔓 Autenticación exitosa. Bienvenido Operador.")
            st.markdown("---")
            
            balances = {eq_nombre: {"partidos": 0, "arbitrajes": 0, "juegos_7pm": 0} for eq_nombre in equipos_map.values()}
            for p in partidos_data:
                if p.get("ganador_id") is not None:
                    loc = equipos_map.get(p["equipo_local_id"])
                    vis = equipos_map.get(p["equipo_visita_id"])
                    arb = equipos_map.get(p["equipo_arbitro_id"])
                    hora = p["hora"]
                    if loc: balances[loc]["partidos"] += 1
                    if vis: balances[vis]["partidos"] += 1
                    if arb: balances[arb]["arbitrajes"] += 1
                    if hora == "7:00 PM":
                        if loc: balances[loc]["juegos_7pm"] += 1
                        if vis: balances[vis]["juegos_7pm"] += 1
            
            # ------------------------------------------
            # 1. ASISTENCIA SEMANAL
            # ------------------------------------------
            st.subheader("1. Confirmación de Equipos Disponibles")
            st.markdown("<small style='color: #94A3B8;'>Marca los equipos que confirmaron asistencia por WhatsApp para este Sábado:</small>", unsafe_allow_html=True)
            
            lista_equipos_ordenada = sorted(list(equipos_map.values()))
            equipos_disponibles = []
            
            cols_asistencia = st.columns(2)
            for idx, eq_nombre in enumerate(lista_equipos_ordenada):
                col_actual = cols_asistencia[idx % 2]
                with col_actual:
                    if st.checkbox(eq_nombre, key=f"chk_{eq_nombre}"):
                        equipos_disponibles.append(eq_nombre)
            
            if "partidos_propuestos" not in st.session_state:
                st.session_state.partidos_propuestos = []
            if "error_partido" not in st.session_state:
                st.session_state.error_partido = None
                
            st.markdown("---")
            
            # ------------------------------------------
            # 🧠 FUNCIÓN MAESTRA DE VALIDACIÓN (CALLBACK)
            # ------------------------------------------
            def callback_validar_y_agregar(local_eq, visita_eq, arbitro_eq, cancha, hora):
                if local_eq == "—" or visita_eq == "—" or arbitro_eq == "—":
                    st.session_state.error_partido = "❌ Error: Debes seleccionar Local, Visitante y Árbitro."
                    return
                    
                espacio_ocupado = any(p["cancha"] == cancha and p["hora"] == hora for p in st.session_state.partidos_propuestos)
                
                if espacio_ocupado:
                    st.session_state.error_partido = f"❌ Inconsistencia: El espacio {cancha} a las {hora} ya está ocupado en este rol."
                    return
                    
                st.session_state.error_partido = None
                st.session_state.partidos_propuestos.append({
                    "jornada": 3,
                    "fecha": "2026-06-06",
                    "hora": hora,
                    "cancha": cancha,
                    "local": local_eq,
                    "visita": visita_eq,
                    "arbitro": arbitro_eq
                })

            # ------------------------------------------
            # 2. INTERFAZ DEL ASISTENTE DE EMPAREJAMIENTO
            # ------------------------------------------
            st.subheader("2. Programar Partido del Sábado")
            col_l, col_v, col_a = st.columns(3)
            with col_l:
                local = st.selectbox("Equipo Local", ["—"] + equipos_disponibles)
            with col_v:
                opciones_v = [e for e in equipos_disponibles if e != local]
                visita = st.selectbox("Equipo Visitante", ["—"] + opciones_v)
            with col_a:
                opciones_a = [e for e in equipos_disponibles if e != local and e != visita]
                arbitro = st.selectbox("Equipo Árbitro", ["—"] + opciones_a)
                
            col_can, col_hor = st.columns(2)
            with col_can:
                cancha_sel = st.selectbox("Cancha de Juego", ["Cancha 1", "Cancha 2"])
            with col_hor:
                hora_sel = st.selectbox("Horario de Juego", ["8:00 PM", "9:00 PM"])
                
            st.button(
                "Validar e Incorporar Juego al Rol Semanal",
                on_click=callback_validar_y_agregar,
                args=(local, visita, arbitro, cancha_sel, hora_sel)
            )
            
            if st.session_state.error_partido:
                st.error(st.session_state.error_partido)

            # ------------------------------------------
            # 3. MUESTRA LA COLA Y SUBE A SUPABASE
            # ------------------------------------------
            if st.session_state.partidos_propuestos:
                st.markdown("---")
                st.subheader("📋 Vista Previa del Nuevo Rol Semanal")
                
                for idx, juego in enumerate(st.session_state.partidos_propuestos):
                    st.text(f"🔹 Juego {idx+1}: [{juego['cancha']} - {juego['hora']}] {juego['local']} vs {juego['visita']} (Pita: {juego['arbitro']})")
                
                if st.button("🗑️ Limpiar Cola de Partidos"):
                    st.session_state.partidos_propuestos = []
                    st.session_state.error_partido = None
                    st.st.rerun()

                st.markdown("---")
                
                if st.button("🚀 ENVIAR ROL DE JORNADA 3 A PRODUCCIÓN", type="primary"):
                    with st.spinner("Actualizando rol en Supabase de forma segura..."):
                        try:
                            nombre_a_id = {v: k for k, v in equipos_map.items()}
                            
                            datos_supabase = []
                            for p in st.session_state.partidos_propuestos:
                                datos_supabase.append({
                                    "jornada": int(p["jornada"]),
                                    "fecha": p["fecha"],
                                    "hora": p["hora"],
                                    "cancha": p["cancha"],
                                    "equipo_local_id": nombre_a_id.get(p["local"]),
                                    "equipo_visita_id": nombre_a_id.get(p["visita"]),
                                    "equipo_arbitro_id": nombre_a_id.get(p["arbitro"]),
                                    "ganador_id": None,
                                    "perdedor_id": None
                                })
                            
                            # PROTECCIÓN DE HISTORIAL: Borra el rol anterior de la J3 que NO se ha jugado aún
                            supabase.table("partidos")\
                                    .delete()\
                                    .eq("jornada", 3)\
                                    .is_("ganador_id", "null")\
                                    .execute()
                            
                            # Inserción del nuevo rol modificado
                            supabase.table("partidos").insert(datos_supabase).execute()
                            
                            # Limpieza forzada de caché para actualización instantánea en la web
                            st.cache_data.clear()
                            
                            st.balloons()
                            st.success("¡Rol publicado exitosamente! Las modificaciones ya están en vivo.")
                            st.session_state.partidos_propuestos = []
                            st.session_state.error_partido = None
                            st.rerun()
                            
                        except Exception as error_db:
                            st.error(f"❌ Error al guardar en la base de datos: {error_db}")
                            
        elif password_admin != "":
            st.error("❌ Clave de administrador incorrecta.")
            
    except KeyError:
        st.error("❌ **Error de Configuración:** No se encontró la variable 'ADMIN_PASSWORD' en los Secrets de Streamlit.")