import csv
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def exportar_rol_legible():
    print("🔄 Descargando datos de Supabase...")
    
    # 1. Traer los equipos para armar un diccionario de IDs a Nombres
    res_equipos = supabase.table("equipos").select("id, nombre").execute()
    equipos_map = {eq["id"]: eq["nombre"] for eq in res_equipos.data}
    
    # 2. Traer todos los partidos ordenados
    res_partidos = supabase.table("partidos").select("*").order("jornada").execute()
    partidos = res_partidos.data
    
    nombre_archivo = "rol_juegos_legible.csv"
    
    # 3. Escribir el archivo CSV cruzando los datos
    with open(nombre_archivo, mode="w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        
        # Cabeceras legibles
        writer.writerow(["Jornada", "Fecha", "Hora", "Cancha", "Equipo Local", "Equipo Visitante", "Equipo Arbitro"])
        
        for p in partidos:
            local = equipos_map.get(p["equipo_local_id"], "Desconocido")
            visita = equipos_map.get(p["equipo_visita_id"], "Desconocido")
            arbitro = equipos_map.get(p["equipo_arbitro_id"], "N/A")
            
            writer.writerow([
                p["jornada"],
                p["fecha"],
                p["hora"],
                p["cancha"],
                local,
                visita,
                arbitro
            ])
            
    print(f"🎉 ¡Archivo creado con éxito! Busca '{nombre_archivo}' en tu carpeta.")

if __name__ == "__main__":
    exportar_rol_legible()