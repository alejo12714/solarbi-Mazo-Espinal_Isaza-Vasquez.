# solarbi-Mazo-Espinal_Isaza-Vasquez.

Javier Isaza Vasquez
Diego Alejandro Mazo Espinal

Curso: Inteligencia de negocios
Grupo: 050

## Descripción del Proyecto

Este repositorio alberga la solución al proyecto **SolarBI Pascual** para la asignatura de Inteligencia de Negocios (Grupo 50), enfocado en la evaluación de la calidad de los datos, el rendimiento energético (*yield*) y el ahorro económico. A través de una arquitectura por capas (Bronze, Silver y Gold) en PostgreSQL, el proyecto integra la simulación de telemetría IoT, un flujo ETL automatizado e idempotente en Python y la visualización comparativa entre Grafana OSS para el monitoreo operativo en tiempo real y Power BI para el análisis analítico y estratégico, todo enmarcado en prácticas formales de gobernanza de datos y control de versiones con Git.

## Pasos para Reproducir la Práctica

### Prerrequisitos

* **Python 3.10+** instalado.
* **PostgreSQL** instalado y en ejecución local.
* **Git**.
* **Grafana OSS** (opcional para el monitoreo operativo).
* **Power BI Desktop** (opcional para el reporte ejecutivo).

### 1. Clonar el repositorio

Abre la terminal y clona el proyecto en tu equipo

### 2. Instalar dependencias requeridas

Ejecuta el siguiente comando en la terminal para instalar las librerías necesarias en tu instalación global de Python:

py -m pip install pandas psycopg2-binary python-dotenv


### 3. Configurar las variables de entorno (`.env`)

Crea un archivo llamado `.env` en la raíz del proyecto (basándote en `.env.example`):

DB_HOST=localhost
DB_PORT=5432
DB_NAME=solarbi
DB_USER=postgres
DB_PASSWORD=tu_contraseña_aqui

### 4. Inicializar la base de datos en PostgreSQL

1. Abre pgAdmin y crea una base de datos llamada `solarbi`.
2. Ejecuta el siguiente script "creacion_tablas" para crear los esquemas y las tablas requeridas:

### 5. Ejecutar el Pipeline ETL

Corre el script principal para generar los datos crudos (Bronze), aplicar la limpieza de calidad (Silver) y consolidar la métrica diaria de energía (Gold):

py etl/run_etl.py

###6. Configuración de Visualizaciones

* **Grafana:**
1. Inicia sesión en Grafana (`http://localhost:3000`).
2. Conecta la base de datos PostgreSQL `solarbi` en **Connections -> Data Sources**.
3. Ve a **Dashboards -> Import** y carga el archivo `grafana/dashboard.json`.


* **Power BI:**
1. Abre Power BI Desktop y selecciona **Obtener datos -> PostgreSQL**.
2. Apunta a la tabla `dwh.fact_energia_dia` para construir los indicadores de Yield y Ahorro financiero.

________________________________________________
### Archivo | Responsable                           
PDF: trabajo en conjunto de los dos integrantes 
Creacion Inicial del repositorio: Diego Mazo   
Data Silver: Javier Isaza                     
Creacion BD en PGadmin4: Diego Mazo            
Power BI: Javier Isaza                      
Grafana: Diego Mazo                             
etl: Javier Isaza y Diego Mazo                  

