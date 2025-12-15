# CyberMind

# Proyecto CyberMind – Plataforma Abierta de Análisis de Información

**CyberMind** es una plataforma modular, automatizada y de código abierto para la recolección, análisis y visualización de información relevante sobre Las vulnerabilidades IT y OT (Tecnologías de la Información y Tecnologías de Operación). Su objetivo es facilitar el acceso a datos estructurados y procesados a partir de fuentes públicas, con enfoque en la transparencia, la colaboración abierta y el uso de metodologías de inteligencia.

El proyecto está orientado tanto a investigadores, periodistas de datos y analistas, como a desarrolladores interesados en contribuir con nuevas funcionalidades y dominios de análisis.

Documentación principal y enlaces rápidos.


## Documentación (Docs)
- Documentacion del proyecto: [Documentacion](Docs/Indice.md)

## Ejecución del programa

- Crear y activar el entorno virtual: sigue la guía en [Docs/instalacion_dependencias.md](Docs/instalacion_dependencias.md).

- Levantar los servicios de soporte (OpenSearch + Dashboards y TinyRSS) usando Docker Compose. Hay un `docker-compose` preparado en `Install/opensearch-compose.yml` y `Install/tinytinyrss.yml`. Para lanzar OpenSearch y Dashboards:

```powershell
cd Install
docker compose -f opensearch-compose.yml up -d
```

- Para TinyRSS (si lo necesitas) puedes lanzar el otro compose:

```powershell
docker compose -f tinytinyrss.yml up -d
```

- Ejecutar la API / UI (desde la raíz del proyecto):

```powershell
python -m src.main
```

- Puedes interactuar con la API en `http://127.0.0.1:8000/docs` (Swagger UI).

## Uso centralizado desde la UI

La interfaz web servida en `/ui` actúa como el panel de control principal de la plataforma. Desde esa UI puedes:

- Ejecutar y controlar scrapers (Google Dorking, Google Alerts, TinyRSS import).
- Iniciar/parar workers y procesos background (Spacy, LLM updater, extractores periódicos).
- Consultar el estado del sistema y ver logs resumidos (vía `GET /status`).
- Ejecutar cualquier endpoint de la API sin salir de la interfaz (la UI hace las llamadas a los endpoints documentados en `Docs/api_endpoints.md`).

El endpoint `main.py` arranca la API FastAPI y la UI; por tanto, levantar el servicio principal posibilita gestionar toda la plataforma desde la página `http://127.0.0.1:8000/ui`.

### Chat integrado: CyberSentinel

La UI incluye un chat llamado **CyberSentinel** que permite interaccionar con el LLM especializado en ciberseguridad (CVE, análisis técnico y resúmenes de noticias). El chat está disponible en la vista `CyberSentinel IA` de la interfaz y envía consultas al endpoint `/llm/query`.

### Recomendaciones de despliegue

- Para uso intensivo del LLM (queries frecuentes o finetuning), se recomienda un equipo con GPU para evitar sobrecarga en CPU/RAM y reducir latencias. Si el LLM se ejecuta en hardware local, habilitar GPU acelera la inferencia y entrenamiento.

### Servicios que arranca la aplicación

Al iniciar la aplicación principal (`main.py`), el proceso puede iniciar o comprobar los servicios configurados (por ejemplo, levantar contenedores Docker para OpenSearch o TinyRSS si así está configurado, y arrancar el componente LLM/local runner cuando esté habilitado). Comprueba la configuración en `Install/` y los ajustes en `cfg.ini` antes del despliegue automático.

### Acceso a Dashboards y TinyRSS desde la UI

La UI embedea (via iframes) las interfaces de OpenSearch Dashboards y TinyRSS; desde el panel principal puedes abrir esas UIs sin salir de `http://127.0.0.1:8000/ui`.
Nota: la instalación manual de OpenSearch todavía está documentada en `Docs/opensearch_install.md` como alternativa, pero el camino recomendado es usar `docker compose`.

## Visualización de los datos

-Para visualizar los datos scrapeados podemos observar el archivo [Result.json] del directorio [Outputs]

-Para visualizar los datos procesados con spacy podemos observar el archivo [Labels_Result.json] del directorio[Outputs]

-Para visualizar los datos almacenados en la BBDD [OpenSearch] puedes usar curl o acceder al Dashboards.

Ver los índices (curl):

```bash
curl -X GET "http://localhost:9200/_cat/indices?v"
```

Ver el indice de scrapy_documents

```bash
curl -X GET "http://localhost:9200/scrapy_documents/_search?pretty"
```

Ver el indice de spacy_documents

```bash
curl -X GET "http://localhost:9200/spacy_documents/_search?pretty"
```

-Para visualizar los datos almacenados en la BBDD [Opensearch] desde el DashBoard accederemos a la siguiente web si el dhasboard esta levantado [DashBoard](http://localhost:5601/).
