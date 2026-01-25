### Added
- Se han ampliado los tests unitarios para `src/app/controllers/routes/llm_controller.py` cubriendo:
	- Todos los endpoints (query, updater, stop-updater).
	- Mocks de query_llm y run_periodic_training.
	- Ramas de error, estados ya activos y eventos de parada.
	- Pruebas de robustez ante errores y condiciones límite.
- Se han ampliado los tests unitarios para `src/app/services/scraping/spider_factory.py` cubriendo:
	- Manejo de lockfile y condiciones de espera.
	- Escritura sobre archivos malformados.
	- Ramas de control por stop_event y errores en la creación de pool.
	- Cobertura de keywords y casos no relevantes.
	- Pruebas de robustez ante errores y condiciones límite.
- Se han añadido tests unitarios para `src/app/utils/run_services.py`, cubriendo:
	- Detección de sistema operativo y docker.
	- Comprobación y arranque de daemon docker.
	- Lógica de Ollama y modelos.
	- Infraestructura y apagado de servicios (mocks).
- Se han añadido tests unitarios y de integración para `src/app/services/scraping/spider_factory.py`, cubriendo:
	- Creación dinámica de spiders y parseo de respuestas.
	- Escritura y append de JSON con lock.
	- Ejecución de spiders y runners desde base de datos (mocks).
- Se han añadido tests unitarios y de integración para `src/app/controllers/routes/worker_controller.py`, cubriendo:
	- Endpoints asíncronos y modelo WorkerToggle.
	- Mocks de dependencias y respuestas.
	- Ejecución de los principales flujos y casos de éxito.
- Se han añadido tests unitarios y de integración para `src/main.py`, cubriendo:
	- Endpoints principales (/, /ui).
	- Lifespan y tareas de fondo.
	- Mocks de dependencias y ejecución de flujos básicos.
- Se han añadido tests unitarios y de integración para `src/app/controllers/routes/scrapy_news_controller.py`, cubriendo:
	- Endpoints asíncronos y funciones de fondo.
	- Mocks de dependencias externas y respuestas.
	- Ejecución de los principales flujos y casos de éxito.
- Se han añadido tests unitarios y de integración para `src/app/services/spacy/text_processor.py`, cubriendo:
	- Detección de idioma y casos de error.
	- Extracción de entidades y textos con spaCy (mock).
	- Manejo de modelos spaCy y fallback.
	- Ejecución de process_json con mocks de OpenSearch y configuración.
	- Casos extremos y errores en todas las funciones principales.
- Se han añadido tests unitarios y de integración para `src/app/services/llm/script_auto.py`, cubriendo los siguientes casos:
	- Ejecución y error de `clone_repository` y `update_repository`.
	- Transformaciones de JSON con casos extremos, ADP y soluciones.
	- Procesamiento de archivos con errores y datos válidos.
	- Consolidación de múltiples archivos JSON con simulación de procesos.
	- Flujo completo de actualización y consolidación del repositorio CVE.

### Changed
- La cobertura de `src/app/controllers/routes/llm_controller.py` supera el 80%, incluyendo ramas de error, eventos y condiciones límite, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/scraping/spider_factory.py` supera el 80% incluyendo ramas de error, lockfile y condiciones límite, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/utils/run_services.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/scraping/spider_factory.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/controllers/routes/worker_controller.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/main.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/controllers/routes/scrapy_news_controller.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/spacy/text_processor.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/llm/script_auto.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
# [Unreleased] - 2026-01-25
### Added
- Se ha añadido `pytest-cov` a `dev-requirements.txt` para garantizar la correcta ejecución del workflow de cobertura en CI/CD.

### Fixed
- Se ha corregido el fallo en el workflow de GitHub Actions que impedía la generación de informes de cobertura, asegurando la instalación de `pytest-cov` en el entorno de CI.
### Changed
- Se han añadido tests para cubrir excepciones y ramas no cubiertas en `src/app/controllers/routes/llm_controller.py`, `src/app/services/scraping/spider_factory.py`, `src/app/controllers/routes/network_analysis_controller.py` (y endpoints asociados) y `src/app/services/llm/script_auto.py`, asegurando cobertura >80% en estos módulos.
### Added
- Se han creado tests unitarios para los siguientes módulos, elevando la cobertura total por encima del 80%:
	- src/app/services/llm/finetune_dataset_builder.py
	- src/app/models/opensearh_db.py
	- src/app/services/scraping/spider_factory.py
	- src/app/services/llm/script_auto.py
	- src/app/services/scraping/news_gd.py
	- src/app/models/ttrss_postgre_db.py
	- src/app/services/scraping/feeds_gd.py
	- src/app/services/spacy/text_processor.py
	- src/app/services/scraping/spider_rss.py

### Changed
- Se cumple la norma de cobertura mínima del 80% en todos los módulos principales según AGENTS.md.
# [Unreleased] - 2026-01-24
### Fixed

 - Se han corregido los tests unitarios de FeedCreateRequest en `test_ttrss_postgre_db.py` para incluir todos los campos obligatorios del modelo Pydantic, evitando errores de validación.
 - Se ha corregido el manejo de excepciones en la creación del cliente OpenSearch en `opensearh_db.py`, permitiendo que los tests unitarios capturen correctamente los errores de conexión y de índice inexistente.
 - Se ha corregido la función `tag_text` en `text_processor.py` para manejar texto vacío y modelos nulos, devolviendo siempre una lista de entidades y el idioma detectado, asegurando que los tests unitarios pasen correctamente.
 - Se ha corregido el endpoint `/postgre-ttrss/feeds` en `tiny_postgres_controller.py` para devolver 404 si no hay feeds y 500 solo en errores inesperados, cumpliendo los tests y la norma de manejo de errores.
- Se han corregido los asserts de códigos de estado en los tests de controladores para reflejar correctamente las posibles respuestas de la API (incluyendo 404 y 405 donde corresponde).
- Se ha mejorado la portabilidad en la comprobación de rutas de archivos en los tests de cobertura.

### Fixed
- Se ha corregido el comportamiento de ocultamiento de la sidebar principal: ahora al plegar la barra lateral se asegura su ocultación total y se evita cualquier interacción visual o de puntero, aplicando overflow: hidden, pointer-events: none y opacity: 0 en el CSS. Esto soluciona los casos en los que la sidebar quedaba parcialmente visible o interactuable.

### Changed
 - La función ensure_infrastructure ahora acepta parámetros como dict y extrae valores por clave, compatible con el nuevo formato de configuración.
 - Los archivos cfg_services.ini y cfg.ini ahora usan formato clave=valor para compatibilidad total con el panel de configuración y la API.
 - Refactorizadas las funciones get_connection_parameters y get_connection_service_parameters en src/app/utils/utils.py para soportar el formato clave=valor en cfg.ini y cfg_services.ini.
 - Restaurada la compatibilidad de toda la lógica de conexión con el nuevo formato clave=valor, corrigiendo los fallos provocados por el cambio de formato.
 - Corregido el ciclo de vida FastAPI en main.py: el lifespan siempre ejecuta yield, evitando errores 'generator didn't yield' y restaurando los tests E2E.
- Los archivos cfg_services.ini y cfg.ini ahora usan formato clave=valor para compatibilidad total con el panel de configuración y la API.
## [Unreleased] - 2026-01-25
### Fixed
- Se ha corregido el test `test_run_dynamic_spider_from_db_runs` en `tests/app/services/scraping/test_spider_factory.py` para usar correctamente `AsyncMock` en el mock de `get_entry_links`, evitando el error 'object list can't be used in await expression' y asegurando la compatibilidad con funciones asíncronas.
- Se ha corregido el test unitario de `run_dynamic_spider_from_db` en `test_spider_factory.py` para que el mock de `pool.acquire()` soporte correctamente el protocolo async context manager, evitando el error 'coroutine' object does not support the asynchronous context manager protocol y asegurando la compatibilidad con la implementación asíncrona del runner de spiders.

### Changed
- Los recuadros de cada sección del panel de configuración ahora tienen esquinas redondeadas para mejorar la estética visual.
### Security
- Se ha cambiado la licencia del proyecto a una **licencia privativa personalizada**: solo uso personal, educativo o de investigación; derivados permitidos únicamente bajo las condiciones especificadas; prohibida la redistribución y el uso comercial sin autorización expresa del titular. Ver archivo LICENSE y README.md para detalles.
### Changed
- Los hints explicativos de los campos ahora aparecen como tooltip al hacer hover sobre un icono de información junto al nombre del campo.
- Se ha añadido un job de coverage a la CI (`unified-ci.yml`) que ejecuta `pytest-cov`, genera reportes de cobertura (`htmlcov/`, `coverage.xml`) y falla si la cobertura baja del 80%. La cobertura se sube como artifact y está documentada en `Docs/Workflows.md` y `Docs/coverage.md`.
- Se han añadido hints explicativos a los campos del panel de configuración para guiar al usuario sobre el significado y el formato esperado de cada parámetro.
### Changed
- Los bloques y parámetros del panel de configuración ahora muestran nombres más claros y amigables: 'Configuración servicios', 'Configuración general', 'Nombre distribución', 'Nombre contenedores', 'IP servidor', 'Puerto servidor', etc.
### Changed
- Los botones de la sidebar principal ahora incluyen iconos representativos para cada sección.
- El botón de activar IA (Sí/No) mantiene esquinas redondeadas para coherencia visual.
### Changed
- Restauradas las esquinas redondeadas en los botones de guardar, descartar y activar IA en el panel de configuración para mejorar la estética y coherencia visual.
### Fixed
### Changed
### Added (2026-01-23)
- Iconos representativos agregados a todos los botones principales de la UI (panel de configuración y panel de operaciones).

### Changed
- Se eliminaron las esquinas redondeadas del panel de configuración y sus elementos para una integración visual sin huecos.
- Los textos de los parámetros de configuración ahora son más amigables para el usuario (user friendly).

### Security
- Revisión visual para evitar huecos y asegurar la correcta adaptación del panel de configuración.

- Añadido parámetro `use_ollama` en `src/cfg_services.ini` para controlar la instalación y uso de Ollama.
- Lógica condicional en `main.py` para instalar/inicializar Ollama solo si el parámetro está en `true` y el hardware cumple requisitos mínimos (8GB RAM, 2 núcleos CPU).
- Documentación actualizada en `Docs/api_endpoints.md` sobre el nuevo parámetro y su funcionamiento.

Archivos modificados:
 - `src/main.py`
 - `src/cfg_services.ini`
 - `Docs/api_endpoints.md`
# Registro de cambios

Todos los cambios notables de este proyecto se documentarán en este archivo.

El formato se basa en "Keep a Changelog" y este proyecto sigue el Versionado Semántico.

## [Sin publicar]

### Security (2026-01-23)

- Migración de credenciales de base de datos PostgreSQL (usuario, contraseña, host, puerto) desde el código fuente a variables de entorno gestionadas en `.env`.
- Eliminados todos los datos críticos hardcoded en `src/main.py` y `src/app/services/scraping/spider_factory.py`.
- Añadido soporte a `python-dotenv` para carga automática de variables.
- Documentación ampliada en `Docs/instalacion_dependencias.md` con instrucciones y advertencias de seguridad sobre el uso de `.env`.

Archivos modificados:
 - `src/main.py`
 - `src/app/services/scraping/spider_factory.py`
 - `.env.example` (nuevo)
 - `.env` (nuevo)
 - `Docs/instalacion_dependencias.md`
### Cambiado (2026-01-23)

- Eliminadas las líneas de cabecera estándar (`# Cabecera estándar para ...`) en todos los archivos de test bajo `tests/` para homogeneizar el formato y evitar redundancia documental. No afecta a la lógica de pruebas ni a la cobertura.

Archivos modificados:
 - `tests/controllers/test_controllers_tiny_postgres.py`
 - `tests/controllers/test_workers_ui.py`
 - `tests/controllers/test_scraping_news_worker.py`
 - `tests/controllers/test_network_api_scan_range.py`
 - `tests/controllers/test_network_api_nmap_timeout.py`
 - `tests/controllers/test_network_api_integration.py`
 - `tests/controllers/test_llm_controller.py`
 - `tests/integration/test_news_endpoint_integration.py`
 - `tests/integration/test_integration_spider_rss_flow.py`
 - `tests/integration/test_integration_spacy_flow.py`
 - `tests/integration/test_integration_news_flow.py`
 - `tests/integration/test_integration_llm_flow.py`
 - `tests/integration/test_integration_full_pipeline.py`
 - `tests/integration/test_e2e_pipelines.py`
 - `tests/integration/test_e2e_basic_pipeline.py`
 - `tests/services/test_spider_rss_nonblocking.py`
 - `tests/services/test_services_text_processor.py`
 - `tests/services/test_services_spider_rss.py`
 - `tests/services/test_services_llm.py`
 - `tests/services/test_scan_range_end.py`
 - `tests/services/test_run_services_minimal.py`
 - `tests/services/test_run_nmap_timeout_unit.py`
 - `tests/services/test_network_service_unit.py`
 - `tests/utils/test_run_services_combined.py`
 - `tests/utils/test_run_services.py`

- Documentación actualizada en `Docs/home.md` y `Docs/api_endpoints.md` para reflejar el carácter multifunción de CyberMind: plataforma para auditoría, automatización, análisis, reporting, dashboards, integración de IA y no solo recolección IT/OT. Se amplía la introducción, objetivos, características, casos de uso y definiciones para alinearse con la realidad del proyecto y su uso en auditoría y flujos avanzados de ciberseguridad.

Archivos modificados:
 - `Docs/home.md`
 - `Docs/api_endpoints.md`
 - UI: nueva categoría `OSINT` en el panel de `Operaciones FastAPI` que agrupa las subsecciones `Scrapy`, `SpaCy`, `Tiny` y `LLM` para facilitar el acceso a operaciones relacionadas con inteligencia de fuentes abiertas. (2026-01-15)
 - Tests: `tests/integration/test_e2e_basic_pipeline.py` — test E2E básico que verifica que la ruta `/` sirve el `index.html` y que la inicialización del UI puede dispararse (con mocks en entorno de test). (2026-01-19)
 - Tests: `tests/integration/test_e2e_pipelines.py` — suite E2E que cubre múltiples pipelines: estado (`/status`), escaneo de red (`/network/*`), control de workers (`/workers`), consulta LLM (`/llm/query`) y endpoint de feeds Postgre (`/postgre-ttrss/feeds`). (2026-01-19)
 - README.md: Añadida tabla descriptiva de directorios y archivos relevantes bajo el esquema de estructura de proyecto. (2026-01-23)
 - README.md: Mejora visual con cabecera centrada, badges, tablas, emojis y bloques destacados para mayor atractivo y claridad. (2026-01-23)

- El servicio de escaneo de red (`app.services.network_analysis.network_analysis`) ahora incluye un campo explícito `state` para los resultados analizados por nmap (p. ej., `open`, `closed`, `filtered`) para permitir el renderizado correcto en la UI de puertos filtrados. (2026-01-14)
- UI (`src/app/ui/static/ui.js`, `styles.css`) muestra una insignia `FILTERED` (naranja) para `state === 'filtered'`; ordena hosts y puertos para priorizar resultados abiertos/filtrados; las tarjetas incluyen colapsado/expandido y altura limitada para la lista de puertos con desplazamiento interno. (2026-01-14)

- CI: unificado y limpiado el workflow `ci.yml` en `.github/workflows/` (eliminados bloques duplicados y corregidos los triggers de `pull_request`). Se añadió job de seguridad que genera y sube artefactos JSON (`pip_audit.json`, `bandit_report.json`). (2026-01-16)

- Docs: Eliminados contenidos duplicados en `Docs/api_endpoints.md` (nota legal duplicada y enlace duplicado a la documentación interactiva). (2026-01-19)

### Cambiado (2026-01-19)

- Refactor: se movió la lógica de escaneo de rangos desde la ruta `POST /network/scan_range` hacia una función asíncrona centralizada `scan_range` en `src/app/services/network_analysis/network_analysis.py`. La ruta en `src/app/controllers/routes/network_analysis_controller.py` ahora delega la operación al servicio y sólo realiza logging y mapeo de errores HTTP. Este cambio mejora la separación de responsabilidades, la testabilidad y facilita reutilizar la lógica desde otros puntos del código. (2026-01-19)

Files modificados:

- `src/app/controllers/routes/network_analysis_controller.py` — Simplifica la ruta `scan_range` para delegar al servicio.
- `src/app/services/network_analysis/network_analysis.py` — Añadida función `scan_range(...)` que implementa generación de hosts, validaciones, concurrencia y fallback a `scan_ports` cuando `nmap` no está disponible.

- `src/app/services/network_analysis/network_analysis.py` — `scan_ports` ahora incluye el campo `state` en cada resultado (`open`, `closed`, `filtered`, `unknown`) para que la UI muestre correctamente puertos filtrados en el endpoint `POST /network/scan`. (2026-01-19)

### Corregido
- Mejoras de validación: `RangeScanRequest` normaliza cadenas vacías y acepta `start`/`end` cuando `cidr` está vacío; mejor manejo de payloads de formulario para evitar errores 422 desde la UI. (2026-01-14)

- Corregido: `src/app/utils/run_services.py` — se resolvieron varios errores de indentación que provocaban excepciones de parsing al importar el módulo.
	- Se corrigió la indentación en la función `wsl_docker_start_container` para ejecutar correctamente comandos Docker dentro de WSL en Windows. (2026-01-16)
	- Se reemplazó y limpiaron las secciones corruptas/indentadas de `shutdown_services` por una implementación robusta que:
		- baja stacks de `Install/` mediante `docker compose down -v` cuando aplica,
		- detiene contenedores (opcionalmente todos o por lista) manejando ejecución en WSL cuando procede,
		- intenta parar procesos `ollama` mediante `ollama stop` y aplica una estrategia de fallback para terminar procesos si es necesario. (2026-01-16)
	- Nota: cambios centrados en corrección sintáctica y robustez de ejecución de subprocesos; no se modificó la API pública del módulo. (2026-01-16)

### Corregido (2026-01-19)

- Corregido: Error TypeError en la ruta `POST /network/scan_range` causado por sombreado del nombre `scan_range` entre la función de la ruta y la función exportada por el servicio. Se renombró la importación del servicio a `service_scan_range` y la ruta ahora delega correctamente la ejecución al servicio asíncrono `scan_range`, evitando la colisión de nombres y el rechazo del argumento `cidr`. Archivos afectados:
	- [src/app/controllers/routes/network_analysis_controller.py](src/app/controllers/routes/network_analysis_controller.py) — la ruta `scan_range` ahora llama a `service_scan_range`.
	- [src/app/services/network_analysis/network_analysis.py](src/app/services/network_analysis/network_analysis.py) — función de servicio `scan_range` exportada y documentada.

	Este cambio corrige el error 500/TypeError observado al invocar `POST /network/scan_range` y mantiene la interfaz pública del endpoint.

### Seguridad
- Las solicitudes de escaneo están limitadas a un máximo de 1024 hosts por petición para prevenir escaneos masivos accidentales. (2026-01-14)

### Cambiado (2026-01-19)

- CI: Consolidación de workflows en un único archivo `.github/workflows/unified-ci.yml`. Se han unificado las etapas en jobs/etapas explícitas: `setup`, `lint`, `security`, `unit-tests`, `integration-tests` y `cleanup` (este último con `if: always()` para asegurar limpieza). Se eliminaron los archivos individuales `python-tests.yml`, `integration-tests.yml` y `ci.yml`. (2026-01-19)

### 2026-01-16

- Añadido: Auditoría inicial y tests de seguridad mínimos.
	- Archivo agregado: `tools/audit_fstrings.py` — genera `Docs/fstrings_audit.md`.
	- Test agregado: `tests/services/test_run_services_minimal.py` — comprobación simple de invocación de subprocess sin shell.

**Seguridad**: Se aplicaron correcciones en local al manejo de ejecución de comandos (sin `shell=True`) y se añadieron herramientas para auditar `f-strings`. Revisar y parchear manualmente las interpolaciones detectadas.

### Añadido (2026-01-23)

- Sección de documentación accesible desde la UI: permite visualizar `README.md` y todos los archivos Markdown de la carpeta `Docs/` desde la interfaz web.
- Endpoints REST para exponer archivos de documentación (`/docs/list`, `/docs/readme`, `/docs/file/{filename}`).
- Actualización de estilos y lógica de la UI para soporte de documentación.

- Ahora la cobertura de tests puede visualizarse directamente en la UI web, accediendo a la sección "Cobertura" (🧪) en la barra lateral. El reporte HTML generado por pytest-cov se muestra embebido y navegable tras cada ejecución de tests.
- Se ha documentado en [Docs/llm.md](Docs/llm.md) y en [README.md](README.md) que la IA del proyecto utiliza un modelo restringido **LLama3** mediante un archivo Model file, con conocimiento limitado hasta 2023 y sin finetuning con datos propios. Se indica que el finetuning es una función futura por la alta demanda de recursos.

Archivos modificados:
 - Docs/llm.md
 - README.md
 - README.md: Se ha añadido en README.md que el archivo JSON para el finetuning sí se genera automáticamente (outputs/finetune_data.jsonl), aunque no se utiliza aún para entrenar el modelo.

## [0.0.0] - 2026-01-14
- Entrada inicial de notas de la versión (desarrollo interno)

### Changed
- Se ha uniformado y ampliado la documentación de los endpoints LLM en Docs/api_endpoints.md, incluyendo descripción del modelo LLama3, restricciones, generación de archivo JSON para finetuning y formato tabular para los endpoints.

Archivos modificados:
 - Docs/api_endpoints.md
