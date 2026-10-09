CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS dwh;

CREATE TABLE IF NOT EXISTS silver.lectura_5min (
    ts TIMESTAMP PRIMARY KEY,
    dispositivo_id INT NOT NULL,
    p_ac_kw NUMERIC(10,3),
    irradiancia_wm2 NUMERIC(10,1),
    temp_modulo_c NUMERIC(10,1)
);

CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
    fecha DATE NOT NULL,
    dispositivo_key INT NOT NULL,
    energia_kwh NUMERIC(10,3),
    pct_datos_validos NUMERIC(5,2),
    PRIMARY KEY (fecha, dispositivo_key)
);