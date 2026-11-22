"""
migrar_multi_torneo.py
======================
Migración para soportar múltiples torneos en la misma base de datos.

PASOS:
  1. Crear tabla `torneos` si no existe.
  2. Insertar Torneo 1 (Liga 1 - Clausura 2026) como CERRADO.
  3. Insertar Torneo 2 (Liga 2) como ACTIVO.
  4. Agregar columna `torneo_id` a `partidos` y asignar torneo_id=1
     a todos los registros existentes.

EJECUCIÓN:
  py migrar_multi_torneo.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Variables de entorno SUPABASE_URL o SUPABASE_KEY no configuradas en .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    print("=" * 55)
    print("  MIGRACIÓN MULTI-TORNEO — LIGA LA CHONA")
    print("=" * 55)

    # ----------------------------------------------------------
    # PASO 1: Verificar si ya existe la tabla torneos
    # ----------------------------------------------------------
    print("\n📋 PASO 1: Verificando tabla 'torneos'...")
    try:
        res = supabase.table("torneos").select("id").limit(1).execute()
        print(f"   ✅ Tabla 'torneos' ya existe ({len(res.data)} registros encontrados).")
        tabla_torneos_existe = True
    except Exception as e:
        print(f"   ⚠️  Tabla 'torneos' no encontrada: {e}")
        print("   📌 Por favor crea la tabla manualmente en Supabase con este SQL:")
        print("""
   CREATE TABLE public.torneos (
     id          SERIAL PRIMARY KEY,
     nombre      TEXT NOT NULL,
     descripcion TEXT,
     fecha_inicio DATE,
     fecha_fin    DATE,
     activo       BOOLEAN NOT NULL DEFAULT false,
     created_at   TIMESTAMPTZ DEFAULT now()
   );
   -- Habilitar RLS y dar acceso público de lectura:
   ALTER TABLE public.torneos ENABLE ROW LEVEL SECURITY;
   CREATE POLICY "Lectura pública torneos"
     ON public.torneos FOR SELECT USING (true);
        """)
        tabla_torneos_existe = False

    # ----------------------------------------------------------
    # PASO 2: Verificar/Insertar Torneo 1
    # ----------------------------------------------------------
    if tabla_torneos_existe:
        print("\n🏆 PASO 2: Verificando Torneo 1 (Clausura 2026)...")
        res_t1 = supabase.table("torneos").select("id, nombre, activo").execute()
        torneos_existentes = res_t1.data

        ids_existentes = [t["id"] for t in torneos_existentes]

        if 1 not in ids_existentes:
            supabase.table("torneos").insert({
                "id": 1,
                "nombre": "Torneo 1 — Clausura 2026",
                "descripcion": "Primera liga. Campeón: por definir.",
                "fecha_inicio": "2026-05-23",
                "fecha_fin": "2026-11-07",
                "activo": False
            }).execute()
            print("   ✅ Torneo 1 insertado.")
        else:
            print(f"   ✅ Torneo 1 ya existe: '{[t['nombre'] for t in torneos_existentes if t['id']==1][0]}'")

        # ----------------------------------------------------------
        # PASO 3: Verificar/Insertar Torneo 2
        # ----------------------------------------------------------
        print("\n🏆 PASO 3: Verificando Torneo 2 (nueva liga)...")
        if 2 not in ids_existentes:
            nombre_t2 = input("   📝 Nombre para el Torneo 2 (ej. 'Torneo 2 — Apertura 2027'): ").strip()
            if not nombre_t2:
                nombre_t2 = "Torneo 2 — Apertura 2027"
            supabase.table("torneos").insert({
                "id": 2,
                "nombre": nombre_t2,
                "descripcion": "Segunda liga en curso.",
                "activo": True
            }).execute()
            print(f"   ✅ Torneo 2 insertado como ACTIVO: '{nombre_t2}'")
        else:
            print(f"   ✅ Torneo 2 ya existe: '{[t['nombre'] for t in torneos_existentes if t['id']==2][0]}'")

    # ----------------------------------------------------------
    # PASO 4: Agregar columna torneo_id a partidos
    # ----------------------------------------------------------
    print("\n📋 PASO 4: Verificando columna 'torneo_id' en tabla 'partidos'...")
    res_pt = supabase.table("partidos").select("id, torneo_id").limit(3).execute()
    
    if res_pt.data and "torneo_id" in res_pt.data[0]:
        # Verificar cuántos tienen NULL o no tienen asignado
        res_sin_torneo = supabase.table("partidos").select("id").is_("torneo_id", "null").execute()
        sin_asignar = len(res_sin_torneo.data)
        
        if sin_asignar > 0:
            print(f"   ⚠️  {sin_asignar} partidos sin torneo_id. Asignando torneo_id=1...")
            # Supabase no soporta UPDATE sin filtro, usamos .neq para todos
            supabase.table("partidos").update({"torneo_id": 1}).is_("torneo_id", "null").execute()
            print(f"   ✅ {sin_asignar} partidos actualizados con torneo_id=1")
        else:
            print("   ✅ Todos los partidos ya tienen torneo_id asignado.")
    else:
        print("   ⚠️  La columna 'torneo_id' NO existe en 'partidos'.")
        print("   📌 Por favor ejecuta este SQL en el editor de Supabase:")
        print("""
   -- Agregar columna torneo_id a partidos:
   ALTER TABLE public.partidos
     ADD COLUMN IF NOT EXISTS torneo_id INTEGER REFERENCES public.torneos(id);

   -- Asignar todos los partidos existentes al Torneo 1:
   UPDATE public.partidos SET torneo_id = 1 WHERE torneo_id IS NULL;

   -- Hacer la columna obligatoria (opcional, después de asignar):
   -- ALTER TABLE public.partidos ALTER COLUMN torneo_id SET NOT NULL;
        """)

    # ----------------------------------------------------------
    # PASO 5: Reporte final
    # ----------------------------------------------------------
    print("\n" + "=" * 55)
    print("  ✅ VERIFICACIÓN COMPLETADA")
    print("=" * 55)
    
    try:
        torneos = supabase.table("torneos").select("id, nombre, activo").execute()
        print("\n🏆 Torneos registrados:")
        for t in torneos.data:
            estado = "🟢 ACTIVO" if t["activo"] else "🔴 Cerrado"
            print(f"   [{t['id']}] {t['nombre']} — {estado}")
        
        total_partidos = supabase.table("partidos").select("id", count="exact").execute()
        print(f"\n⚽ Total de partidos en BD: {total_partidos.count}")
        
        for t in torneos.data:
            pts_torneo = supabase.table("partidos").select("id", count="exact").eq("torneo_id", t["id"]).execute()
            print(f"   Torneo {t['id']}: {pts_torneo.count} partidos")
    except Exception as e:
        print(f"   (No se pudo obtener reporte: {e})")

    print("\n🎉 ¡Migración completada! Próximos pasos:")
    print("   1. Actualiza app.py (ya incluye selector de torneo).")
    print("   2. Usa generar_rol_supabase.py con TORNEO_ID = 2 para el nuevo rol.")

if __name__ == "__main__":
    main()
