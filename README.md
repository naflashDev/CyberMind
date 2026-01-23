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
# CyberMind

Proyecto CyberMind – Plataforma abierta de análisis de información para ciberseguridad

## Descripción

`CyberMind` es una plataforma modular y de código abierto diseñada para la recolección, enriquecimiento, análisis y visualización de información relacionada con vulnerabilidades y eventos de ciberseguridad (IT y OT). Está orientada a investigadores, analistas, periodistas de datos y desarrolladores que necesiten procesar feeds, scrapers y pipelines de NLP/LLM para generar alertas, resúmenes y dashboards.

## Stack tecnológico

- Lenguaje: Python 3.10+.
- Web/API: FastAPI (documentación OpenAPI/Swagger).
- Búsqueda/almacenamiento: OpenSearch.
- NLP: SpaCy.
- Modelos LLM: integración con runtimes locales/externos (p. ej. Ollama o backends configurables).
- Scrapers: Scrapy, TinyRSS y adaptadores para Google Alerts/feeds RSS.
- Contenerización: Docker / Docker Compose (ficheros en `Install/`).
- Tests: pytest; CI configurado en `.github/workflows/`.

## Instalación y ejecución

1. Clona el repositorio y sitúate en la raíz del proyecto.

2. Crear y activar entorno virtual (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Revisar `cfg.ini` y `src/cfg_services.ini` para parámetros de entorno (puertos, usuario/clave, endpoints LLM).

4. Servicios opcionales (OpenSearch, Dashboards, TinyRSS):

```powershell
cd Install
docker compose -f opensearch-compose.yml up -d
docker compose -f tinytinyrss.yml up -d  # opcional
```

5. Ejecutar la aplicación principal (API + UI):

```powershell
python -m src.main
```

6. Acceder a:
- Documentación interactiva: `http://127.0.0.1:8000/docs`
- UI principal: `http://127.0.0.1:8000/ui`

## Estructura del proyecto (resumen)

- `src/` — Código fuente principal:
	- `app/` — controladores, modelos, servicios, utils y UI estática.
	- `main.py` — arranque de la aplicación.
- `Docs/` — documentación (endpoints, guías de instalación y configuración).
- `Install/` — compose y ficheros para levantar dependencias (OpenSearch, TinyRSS).
- `tests/` — tests unitarios e integración (`pytest`).
- `tools/` — utilidades y scripts auxiliares.
- `data/`, `outputs/` — datos de entrada y artefactos generados.

## Funcionalidades principales

- Recolección de fuentes: scrapers, importadores RSS y Google Alerts.
- Pipeline de procesamiento con SpaCy (extracción de entidades, normalización).
- Almacenamiento y búsqueda en OpenSearch; Dashboards para visualización.
- Endpoints REST para control de pipelines, escaneos de red, consultas LLM y estado del sistema.
- UI integrada con chat `CyberSentinel` para consultas LLM y gestión de workflows.

## Contribuir

- Lee la documentación en `Docs/Indice.md` y `Docs/api_endpoints.md` antes de proponer cambios.
- Añade tests para cambios funcionales y documenta cualquier endpoint nuevo en `Docs/api_endpoints.md`.

Para ejecutar tests localmente:

```powershell
pip install -r dev-requirements.txt
pytest -q
```

## Registro de cambios

Consulta `Docs/ChangeLog.md` para ver el historial de cambios.

## Licencia

Revisa `LICENSE` en la raíz del repositorio.

---
Archivo actualizado: 2026-01-23
