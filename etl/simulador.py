import csv
import math
import os
import random
from datetime import datetime, timedelta

random.seed(42)

inicio = datetime(2026, 10, 5, 0, 0)
os.makedirs("data/bronze", exist_ok=True)

with open("data/bronze/telemetria.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"])

    for i in range(3 * 288):
        ts = inicio + timedelta(minutes=5 * i)
        sol = max(0.0, math.sin(math.pi * (ts.hour + ts.minute / 60 - 6) / 12))
        irr = round(1000 * sol * random.uniform(0.7, 1.0), 1)
        p_ac = round(5.0 * irr / 1000 * random.uniform(0.80, 0.90), 3)
        temp = round(22 + 30 * sol, 1)

        fila = [ts.isoformat(sep=" "), 1, p_ac, irr, temp]
        duplicar = False

        r = random.random()
        if r < 0.02:
            fila[2] = -1
        elif r < 0.04:
            fila[3] = ""
        elif r < 0.05:
            fila[4] = 120.0
        elif r < 0.06:
            duplicar = True

        w.writerow(fila)
        if duplicar:
            w.writerow(fila)