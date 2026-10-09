import os
import csv
import math
import random
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de conexión leyendo desde .env
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "solarbi"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")
}

def generar_bronze():
    inicio = datetime(2026, 10, 5, 0, 0)
    os.makedirs("data/bronze", exist_ok=True)
    ruta_bronze = "data/bronze/telemetria.csv"
    
    with open(ruta_bronze, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"])
        for i in range(3 * 288):  # 3 días, cada 5 min
            ts = inicio + timedelta(minutes=5 * i)
            sol = max(0.0, math.sin(math.pi * (ts.hour + ts.minute / 60 - 6) / 12))
            irr = round(1000 * sol * random.uniform(0.7, 1.0), 1)
            p_ac = round(5.0 * irr / 1000 * random.uniform(0.80, 0.90), 3)
            fila = [ts.isoformat(sep=" "), 1, p_ac, irr, round(22 + 30 * sol, 1)]
            
            r = random.random()
            if r < 0.02:
                fila[2] = -1  # anomalía: potencia negativa
            elif r < 0.04:
                fila[3] = ""  # anomalía: dato faltante
            w.writerow(fila)
            if r > 0.98:
                w.writerow(fila)  # anomalía: fila duplicada
    return ruta_bronze

def procesar_silver(ruta_bronze):
    P_MAX_KW, IRR_MAX, TEMP_MIN, TEMP_MAX = 6.0, 1500, -10, 80
    os.makedirs("data/silver", exist_ok=True)
    
    df = pd.read_csv(ruta_bronze)
    filas_leidas = len(df)

    for col in ["p_ac_kw", "irradiancia_wm2", "temp_modulo_c"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Regla 1: Datos faltantes
    mask_faltantes = df.isnull().any(axis=1)
    rechazadas_faltantes = int(mask_faltantes.sum())
    resto = df[~mask_faltantes]

    # Regla 2: Duplicados
    mask_dup = resto.duplicated(subset=["ts", "dispositivo_id"], keep="first")
    rechazadas_duplicados = int(mask_dup.sum())
    resto = resto[~mask_dup]

    # Regla 3: Rango físico válido
    mask_rango = (
        (resto["p_ac_kw"] < 0) | (resto["p_ac_kw"] > P_MAX_KW) |
        (resto["irradiancia_wm2"] < 0) | (resto["irradiancia_wm2"] > IRR_MAX) |
        (resto["temp_modulo_c"] < TEMP_MIN) | (resto["temp_modulo_c"] > TEMP_MAX)
    )
    rechazadas_rango = int(mask_rango.sum())
    df_silver = resto[~mask_rango].copy()

    filas_validas = len(df_silver)
    filas_rechazadas_total = filas_leidas - filas_validas
    pct_validas = (filas_validas / filas_leidas) * 100 if filas_leidas else 0.0

    print("=" * 50)
    print("       REPORTE DE CALIDAD DE DATOS (SILVER)")
    print("=" * 50)
    print(f"Filas leídas (Bronze):           {filas_leidas}")
    print(f"Rechazadas por datos faltantes:   {rechazadas_faltantes}")
    print(f"Rechazadas por duplicados:        {rechazadas_duplicados}")
    print(f"Rechazadas por rango inválido:    {rechazadas_rango}")
    print("-" * 50)
    print(f"Total filas rechazadas:           {filas_rechazadas_total}")
    print(f"Total filas válidas (Silver):     {filas_validas}")
    print(f"Porcentaje de datos válidos:      {pct_validas:.2f}%")
    print("=" * 50)

    df_silver.to_csv("data/silver/telemetria_clean.csv", index=False)
    return df_silver, pct_validas

def cargar_postgresql(df_silver, pct_validas):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Carga a Silver (UPSERT por clave primaria ts)
    sql_silver = """
        INSERT INTO silver.lectura_5min (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c)
        VALUES %s
        ON CONFLICT (ts) DO UPDATE SET
            p_ac_kw = EXCLUDED.p_ac_kw,
            irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
            temp_modulo_c = EXCLUDED.temp_modulo_c;
    """
    valores_silver = [
        (r['ts'], int(r['dispositivo_id']), float(r['p_ac_kw']), float(r['irradiancia_wm2']), float(r['temp_modulo_c']))
        for _, r in df_silver.iterrows()
    ]
    execute_values(cur, sql_silver, valores_silver)

    # Transformación Gold: Energía (kWh) = Potencia (kW) * (5/60 horas)
    df_silver['fecha'] = pd.to_datetime(df_silver['ts']).dt.date
    df_silver['energia_intervalo_kwh'] = df_silver['p_ac_kw'] * (5.0 / 60.0)

    df_gold = df_silver.groupby(['fecha', 'dispositivo_id'])['energia_intervalo_kwh'].sum().reset_index()
    df_gold.rename(columns={'energia_intervalo_kwh': 'energia_kwh'}, inplace=True)

    # Carga a Gold (UPSERT por clave compuesta fecha, dispositivo_key)
    sql_gold = """
        INSERT INTO dwh.fact_energia_dia (fecha, dispositivo_key, energia_kwh, pct_datos_validos)
        VALUES %s
        ON CONFLICT (fecha, dispositivo_key) DO UPDATE SET
            energia_kwh = EXCLUDED.energia_kwh,
            pct_datos_validos = EXCLUDED.pct_datos_validos;
    """
    valores_gold = [
        (r['fecha'], int(r['dispositivo_id']), round(float(r['energia_kwh']), 3), round(pct_validas, 2))
        for _, r in df_gold.iterrows()
    ]
    execute_values(cur, sql_gold, valores_gold)

    conn.commit()

    # Verificación de registros
    cur.execute("SELECT COUNT(*) FROM silver.lectura_5min;")
    cnt_silver = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM dwh.fact_energia_dia;")
    cnt_gold = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"\n[PostgreSQL] Conteo final en 'silver.lectura_5min': {cnt_silver}")
    print(f"[PostgreSQL] Conteo final en 'dwh.fact_energia_dia': {cnt_gold}")

if __name__ == "__main__":
    ruta_b = generar_bronze()
    df_s, pct = procesar_silver(ruta_b)
    cargar_postgresql(df_s, pct)