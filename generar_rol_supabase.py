import datetime
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from ortools.sat.python import cp_model

# ==========================================
# 1. CARGA DE CREDENCIALES DESDE EL .ENV
# ==========================================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Las variables de entorno SUPABASE_URL o SUPABASE_KEY no están configuradas en tu .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 2. PARÁMETROS CONFIGURABLES DE LA LIGA
# ==========================================
NUM_JORNADAS = 8  
CANCHAS = ["Cancha 1", "Cancha 2"]
HORARIOS = ["7:00 PM", "8:00 PM", "9:00 PM"]

# 🎛️ ¡EL INTERRUPTOR DE LAGOS ESTÁ AQUÍ!
LAGOS_DEBUTA_ESTE_SABADO = False  

# 🏆 ID del torneo activo — Cambiar al iniciar cada nueva liga:
#    1 = Liga 1 Clausura 2026 (terminada)
#    2 = Liga 2 (en curso)
TORNEO_ID = 2

def generar_y_subir_rol():
    print("🔄 Conectando a Supabase y absorbiendo datos de los equipos...")
    
    res_equipos = supabase.table("equipos").select("id, nombre, es_foraneo").order("id").execute()
    datos_equipos = res_equipos.data
    
    if len(datos_equipos) != 9:
        print(f"❌ Error: El modelo requiere exactamente 9 equipos en la tabla. Tienes: {len(datos_equipos)}")
        return

    lista_ids = [eq['id'] for eq in datos_equipos]
    nombres_eq = {eq['id']: eq['nombre'] for eq in datos_equipos}
    
    # Identificación dinámica de equipos clave para restricciones
    id_lagos = next((eq['id'] for eq in datos_equipos if eq['es_foraneo']), lista_ids[-1])
    id_cuervos = next((id for id, name in nombres_eq.items() if "cuervos" in name.lower()), None)
    id_santamaria = next((id for id, name in nombres_eq.items() if "santa" in name.lower()), None)
    
    # 📌 NUEVOS IDENTIFICADORES PARA REFACTORIZACIÓN JORNADA 1
    id_halconcitos = next((id for id, name in nombres_eq.items() if "halconcitos" in name.lower()), None)
    id_halcones = next((id for id, name in nombres_eq.items() if "halcones" in name.lower() and "cit" not in name.lower()), None)
    id_cardenales = next((id for id, name in nombres_eq.items() if "cardenales" in name.lower()), None)
    id_titanes = next((id for id, name in nombres_eq.items() if "titanes" in name.lower() or "felinos" in name.lower()), None)
    id_panteras = next((id for id, name in nombres_eq.items() if "panteras" in name.lower()), None)

    print(f"✅ Configuración cargada. Equipo foráneo: {nombres_eq[id_lagos]}")
    print(f"📅 Variante activa: Lagos {'SÍ' if LAGOS_DEBUTA_ESTE_SABADO else 'NO'} juega en la Jornada 1.")

    # ==========================================
    # 3. CREACIÓN DEL MODELO MATEMÁTICO (OR-TOOLS)
    # ==========================================
    model = cp_model.CpModel()

    # Variables principales de partidos
    partidos = {}
    for j in range(NUM_JORNADAS):
        for c in range(len(CANCHAS)):
            for h in range(len(HORARIOS)):
                for e1 in lista_ids:
                    for e2 in lista_ids:
                        if e1 != e2:
                            partidos[j, c, h, e1, e2] = model.NewBoolVar(f'p_{j}_{c}_{h}_{e1}_{e2}')

    # Variables de arbitraje
    arbitros = {}
    for j in range(NUM_JORNADAS):
        for c in range(len(CANCHAS)):
            for h in range(len(HORARIOS)):
                for e in lista_ids:
                    arbitros[j, c, h, e] = model.NewBoolVar(f'a_{j}_{c}_{h}_{e}')

    # Controles de asistencia y asignación de Lagos
    lagos_asiste = [model.NewBoolVar(f'lagos_asiste_{j}') for j in range(NUM_JORNADAS)]
    lagos_en_cancha = {}
    for j in range(NUM_JORNADAS):
        for c in range(len(CANCHAS)):
            lagos_en_cancha[j, c] = model.NewBoolVar(f'lagos_cancha_{j}_{c}')

    # ==========================================
    # 4. RESTRICCIONES DURAS (LOGÍSTICA)
    # ==========================================
    
    # Aplicación de la asistencia de Lagos
    if LAGOS_DEBUTA_ESTE_SABADO:
        model.Add(lagos_asiste[0] == 1)  
    else:
        model.Add(lagos_asiste[0] == 0)  

    # 📌 REFACTORIZACIÓN: FIJACIÓN INYECTADA DE LA JORNADA 1 (index j=0, hora 8:00 PM h=1)
    # Cancha 1 (c=0) -> CARDENALES VS HALCONCITOS | Pita: PANTERAS
    if id_cardenales and id_halconcitos:
        model.Add(partidos[0, 0, 1, id_cardenales, id_halconcitos] + partidos[0, 0, 1, id_halconcitos, id_cardenales] == 1)
    if id_panteras:
        model.Add(arbitros[0, 0, 1, id_panteras] == 1)

    # Cancha 2 (c=1) -> TITANES VS HALCONES | Pita: CUERVOS
    if id_titanes and id_halcones:
        model.Add(partidos[0, 1, 1, id_titanes, id_halcones] + partidos[0, 1, 1, id_halcones, id_titanes] == 1)
    if id_cuervos:
        model.Add(arbitros[0, 1, 1, id_cuervos] == 1)

    # 1. Round Robin perfecto
    for i, e1 in enumerate(lista_ids):
        for e2 in lista_ids[i + 1:]:
            model.Add(sum(partidos[j, c, h, e1, e2] + partidos[j, c, h, e2, e1] 
                          for j in range(NUM_JORNADAS) for c in range(len(CANCHAS)) for h in range(len(HORARIOS))) == 1)

    # 2. Ocupación física de las canchas
    for j in range(NUM_JORNADAS):
        for c in range(len(CANCHAS)):
            for h in range(len(HORARIOS)):
                model.Add(sum(partidos[j, c, h, e1, e2] for e1 in lista_ids for e2 in lista_ids if e1 != e2) <= 1)

    # 3. Intermitencia de Lagos (No semanas consecutivas)
    model.Add(sum(lagos_asiste[j] for j in range(NUM_JORNADAS)) == 4)
    for j in range(NUM_JORNADAS - 1):
        model.Add(lagos_asiste[j] + lagos_asiste[j+1] <= 1)

    # 4. Prioridad y Llenado de Canchas
    for j in range(NUM_JORNADAS):
        for h in [0, 1]:
            for c in range(len(CANCHAS)):
                model.Add(sum(partidos[j, c, h, e1, e2] for e1 in lista_ids for e2 in lista_ids if e1 != e2) == 1)
        
        model.Add(sum(partidos[j, 1, 2, e1, e2] for e1 in lista_ids for e2 in lista_ids if e1 != e2) == 0)
        model.Add(sum(partidos[j, 0, 2, e1, e2] for e1 in lista_ids for e2 in lista_ids if e1 != e2) == lagos_asiste[j])

    # 5. Ritmo de juego estructural
    for j in range(NUM_JORNADAS):
        for e in lista_ids:
            juegos_equipo_hoy = sum(partidos[j, c, h, e, e2] + partidos[j, c, h, e2, e] 
                                    for c in range(len(CANCHAS)) for h in range(len(HORARIOS)) for e2 in lista_ids if e2 != e)
            if e == id_lagos:
                model.Add(juegos_equipo_hoy == 2 * lagos_asiste[j])
            else:
                model.Add(juegos_equipo_hoy == 1)

    # 6. Restricciones espaciales y de continuidad de Lagos
    for j in range(NUM_JORNADAS):
        model.Add(sum(lagos_en_cancha[j, c] for c in range(len(CANCHAS))) == lagos_asiste[j])
        for c in range(len(CANCHAS)):
            juegos_lagos_cancha = sum(partidos[j, c, h, id_lagos, e2] + partidos[j, c, h, e2, id_lagos] for h in range(len(HORARIOS)) for e2 in lista_ids if e2 != id_lagos)
            model.Add(juegos_lagos_cancha == 2 * lagos_en_cancha[j, c])
            
        juegos_lagos_8pm = sum(partidos[j, c, 1, id_lagos, e2] + partidos[j, c, 1, e2, id_lagos] for c in range(len(CANCHAS)) for e2 in lista_ids if e2 != id_lagos)
        model.Add(juegos_lagos_8pm == lagos_asiste[j])

    # ==========================================
    # 5. LOGÍSTICA Y REGLAS DE ARBITRAJE
    # ==========================================
    for j in range(NUM_JORNADAS):
        for c in range(len(CANCHAS)):
            for h in range(len(HORARIOS)):
                hay_juego = sum(partidos[j, c, h, e1, e2] for e1 in lista_ids for e2 in lista_ids if e1 != e2)
                model.Add(sum(arbitros[j, c, h, e] for e in lista_ids) == hay_juego)
                
                for e in lista_ids:
                    juega_aqui = sum(partidos[j, c, h, e, e2] + partidos[j, c, h, e2, e] for e2 in lista_ids if e2 != e)
                    model.Add(arbitros[j, c, h, e] + juega_aqui <= 1)

    # Coherencia horaria de árbitros locales
    for j in range(NUM_JORNADAS):
        for e in lista_ids:
            juega_7 = sum(partidos[j, c, 0, e, e2] + partidos[j, c, 0, e2, e] for c in range(len(CANCHAS)) for e2 in lista_ids if e2 != e)
            juega_8 = sum(partidos[j, c, 1, e, e2] + partidos[j, c, 1, e2, e] for c in range(len(CANCHAS)) for e2 in lista_ids if e2 != e)
            juega_9 = sum(partidos[j, c, 2, e, e2] + partidos[j, c, 2, e2, e] for c in range(len(CANCHAS)) for e2 in lista_ids if e2 != e)
            
            pit_7 = sum(arbitros[j, c, 0, e] for c in range(len(CANCHAS)))
            pit_8 = sum(arbitros[j, c, 1, e] for c in range(len(CANCHAS)))
            pit_9 = sum(arbitros[j, c, 2, e] for c in range(len(CANCHAS)))

            model.Add(pit_7 <= juega_8)  
            model.Add(pit_9 <= juega_8)  
            model.Add(pit_8 <= juega_7 + juega_9)  
            model.Add(pit_7 + pit_8 + pit_9 <= 1)  

    model.Add(sum(arbitros[j, c, h, id_lagos] for j in range(NUM_JORNADAS) for c in range(len(CANCHAS)) for h in range(len(HORARIOS))) == 0)
    
    for e in lista_ids:
        if e != id_lagos:
            total_arbitrajes = sum(arbitros[j, c, h, e] for j in range(NUM_JORNADAS) for c in range(len(CANCHAS)) for h in range(len(HORARIOS)))
            model.Add(total_arbitrajes >= 4)
            model.Add(total_arbitrajes <= 5)

    for e in lista_ids:
        for h in range(len(HORARIOS)):
            model.Add(sum(partidos[j, c, h, e, e2] + partidos[j, c, h, e2, e] 
                          for j in range(NUM_JORNADAS) for c in range(len(CANCHAS)) for e2 in lista_ids if e != e2) <= 4)

    # ==========================================
    # 6. RESTRICCIONES SUAVES (PREFERENCIAS)
    # ==========================================
    penalizaciones = []

    if id_cuervos and id_santamaria:
        for j in [0, 1]:
            for c in range(len(CANCHAS)):
                for h in range(len(HORARIOS)):
                    rivales_jugando = partidos[j, c, h, id_cuervos, id_santamaria] + partidos[j, c, h, id_santamaria, id_cuervos]
                    penalizaciones.append(rivales_jugando * 100)

    if penalizaciones:
        model.Minimize(sum(penalizaciones))

    # ==========================================
    # 7. RESOLVER E INSERTAR EN SUPABASE
    # ==========================================
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("🧠 ¡Estructura de torneo óptima y balanceada calculada con éxito!")
        print(f"\u26bd Generando partidos para Torneo {TORNEO_ID} (sin borrar torneos anteriores)...")

        partidos_nuevos = []
        fecha_base = datetime.date.today()
        
        if fecha_base.weekday() != 5:
            fecha_base += datetime.timedelta(days=(5 - fecha_base.weekday()) % 7)

        for j in range(NUM_JORNADAS):
            fecha_jornada = fecha_base + datetime.timedelta(weeks=j)
            for h in range(len(HORARIOS)):
                for c in range(len(CANCHAS)):
                    for e1 in lista_ids:
                        for e2 in lista_ids:
                            if e1 != e2 and solver.Value(partidos[j, c, h, e1, e2]) == 1:
                                
                                id_arb = None
                                for e_arb in lista_ids:
                                    if solver.Value(arbitros[j, c, h, e_arb]) == 1:
                                        id_arb = e_arb

                                partidos_nuevos.append({
                                    "torneo_id": TORNEO_ID,
                                    "jornada": j + 1,
                                    "fecha": str(fecha_jornada),
                                    "cancha": CANCHAS[c],
                                    "hora": HORARIOS[h],
                                    "equipo_local_id": e1,
                                    "equipo_visita_id": e2,
                                    "equipo_arbitro_id": id_arb
                                })

        print(f"🚀 Subiendo {len(partidos_nuevos)} partidos estructurados a Supabase...")
        supabase.table("partidos").insert(partidos_nuevos).execute()
        print("🎉 ¡Temporada perfecta publicada de forma exitosa!")
    else:
        print("❌ El motor determinó que el cruce de restricciones bloquea matemáticamente la solución.")

if __name__ == "__main__":
    generar_y_subir_rol()