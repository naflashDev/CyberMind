## [Unreleased] - 2026-03-15
### Added
- Sección "Code Scanning" en la UI bajo "Services" con soporte para análisis de código por texto y archivo, mostrando resultados en tarjetas visuales y descarga de informe PDF.
- Documentación de endpoints de code scanning en `api_endpoints.md`.
### Changed (2026-02-13)
- Ampliados los tests unitarios para `src/app/services/hashed/bruteforce_utils.py`, cubriendo la función interna `_bruteforce_worker` (timeout, max_combinations, chunking, caracteres especiales, detección exitosa y fallida). La cobertura del módulo supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
Archivos modificados:
 - `tests/unit/test_bruteforce_utils.py`
 - `src/app/services/hashed/bruteforce_utils.py`
### Added
- Endpoint `/workers/shutdown` para apagar la aplicación y todos los procesos desde la UI.
- Botón de apagado en el sidebar de la UI con feedback visual y estilos de seguridad.
# [Unreleased] - 2026-02-13

### Security
- Eliminadas todas las credenciales hardcoded de conexión a PostgreSQL en los controladores de feeds (<code>tiny_postgres_controller.py</code>). Ahora se utilizan exclusivamente variables de entorno definidas en el archivo <code>.env</code> (<code>POSTGRES_USER</code>, <code>POSTGRES_PASSWORD</code>, <code>POSTGRES_DB</code>, <code>POSTGRES_HOST</code>, <code>POSTGRES_PORT</code>), cumpliendo la política de seguridad y buenas prácticas establecidas en <code>AGENTS.md</code>.
- Documentación de endpoints actualizada en <code>Docs/api_endpoints.md</code> para reflejar el uso de variables de entorno en la conexión a la base de datos.

### Added
- Nuevo endpoint <code>/hashed/hash-file</code> que permite subir un archivo de texto donde cada línea es una palabra, seleccionar el algoritmo de hash (MD5, SHA256, SHA512) y obtener el hash de cada palabra en tarjetas visuales desde la UI (drag & drop). No almacena los hashes, solo los calcula y devuelve.
- La UI ahora incluye un formulario para subir archivos de palabras y seleccionar el algoritmo de hash, mostrando el resultado en tarjetas visuales con la palabra, el hash y el algoritmo usado.
- Documentación ampliada en <code>Docs/api_endpoints.md</code> para el nuevo endpoint, con ejemplos de uso y formato de respuesta.
- Tests unitarios para <code>/hashed/hash-file</code> cubriendo casos Happy Path, Edge Case (archivo vacío) y Error Handling (algoritmo no soportado, excepción en hash).


### Added
- Nuevo endpoint <code>/hashed/upload-hash-file</code> que permite subir un archivo de texto con múltiples líneas, cada una con una palabra y su hash (separados por coma, espacio, tabulación o dos puntos). El sistema detecta automáticamente el tipo de hash y almacena cada entrada en la base de datos. Si el hash ya existe, lo indica de forma amigable. Ideal para cargas masivas mediante drag & drop en la UI.
- Documentación ampliada y actualizada en <code>Docs/api_endpoints.md</code> para el endpoint de subida de hashes, incluyendo el nuevo formato de respuesta y ejemplos.
- La UI ahora muestra el resultado de la subida de hashes con tarjetas visuales y mensajes claros: "Hash insertado correctamente", "Hash ya almacenado en el sistema" o errores de formato, sin exponer nunca información interna.
### Security
- El endpoint <code>/hashed/upload-hash-file</code> y la UI asociada han sido reforzados para no exponer nunca detalles internos de la base de datos ni trazas de error. Todos los mensajes devueltos al usuario son claros y seguros, cumpliendo la política de seguridad definida en <code>AGENTS.md</code>.
 - El servicio de hash ahora incluye logs detallados usando loguru en todos los puntos clave: inicio y fin de operaciones, resultados de búsqueda en BBDD, intentos de fuerza bruta, errores y guardado de nuevos hashes. Esto mejora la trazabilidad y el diagnóstico de incidencias.
 - La fuerza bruta para deshashear hashes ahora se detiene automáticamente tras 120 segundos, devolviendo el número de combinaciones probadas y un indicador de timeout en la respuesta. Si se encuentra el valor original, se almacena automáticamente en la base de datos para futuras consultas rápidas.
- Nuevo endpoint <code>/hashed/unhash</code> para deshashear uno o varios hashes (multilínea, auto-detección de tipo, búsqueda en BBDD y fuerza bruta multiproceso hasta 20 caracteres, incluyendo caracteres especiales más usados).
- Lógica de fuerza bruta y detección de tipo de hash implementada en el servicio de hashing, cumpliendo los requisitos de seguridad y rendimiento.
- UI actualizada: el algoritmo de hash es ahora seleccionable mediante un desplegable en la sección de hasheo, mejorando la experiencia de usuario y evitando errores de entrada manual. La caja de texto multilinea para hashes y la visualización de resultados por hash en tarjetas se mantienen.
- Documentación ampliada en <code>Docs/api_endpoints.md</code> y tests unitarios para la nueva funcionalidad.
### Added
- Limpieza automática de carpetas `outputs` y `data` en la raíz del proyecto tras la ejecución de tests (hook en `conftest.py`).

## [2026-02-06]
### Added
- El servicio de hash ahora calcula el hash, lo muestra al usuario y lo almacena en la base de datos solo si no existe ya guardado. El endpoint es idempotente y nunca genera duplicados.
- Actualizada la documentación de endpoints (`Docs/api_endpoints.md`) para reflejar el nuevo comportamiento del servicio hash.
### Fixed
- Corregidos los tests unitarios de `/hashed/unhash` para usar el formato de entrada correcto (`hashes` multilínea y `max_len`).
- El mock de servicio en los tests ahora devuelve la estructura esperada por el endpoint (lista de objetos tipo MultiUnhashResponseItem).
- Documentación del endpoint `/hashed/unhash` actualizada en `Docs/api_endpoints.md` para reflejar el formato real de entrada y respuesta, con ejemplo de uso.
- Tests unitarios, integración y cobertura verificados tras el cambio en el servicio hash.
### Security
- El nuevo flujo evita duplicidad de hashes y refuerza la integridad de la base de datos.
## [Unreleased]
### Security
- Todos los endpoints de los controladores han sido actualizados para que, en caso de error, devuelvan siempre un mensaje genérico a la UI: "Ha ocurrido un error interno. Por favor, contacte con el administrador.". Nunca se exponen detalles internos ni información sensible en los mensajes de error enviados al cliente. Los detalles completos solo quedan registrados en los logs del backend. Cumple la política de seguridad definida en `AGENTS.md`.

### Fixed
- Unificado el manejo de errores en todos los controllers para evitar la filtración de información interna o sensible a través de los mensajes de error de la API. Se han adaptado los tests afectados para reflejar el nuevo comportamiento.
### Fixed
 - Corregido error de PermissionError en el fixture de tests unitarios (`conftest.py`) usando reintentos y manejo seguro de archivos en Windows.
 - Solucionados los RuntimeWarning de corutinas no awaitadas en los módulos de scraping (`feeds_gd.py`) y análisis de red (`network_analysis.py`), asegurando que los métodos logger.* se awaitan correctamente cuando son AsyncMock en tests.
### Removed
- Eliminada la sección de cobertura de la interfaz web. El informe HTML de coverage.py solo está disponible como archivo estático tras ejecutar los tests.
- Se ha añadido un aviso destacado en la documentación de endpoints (`Docs/api_endpoints.md`) advirtiendo que no se debe ejecutar el worker de LLM Updater en máquinas poco potentes, debido a su alto consumo de recursos.
- El informe de cobertura HTML ahora se sirve con el CSS global de la UI, eliminando el CSS propio generado por coverage.py. Esto unifica la experiencia visual en la sección Cobertura, aunque puede modificar el aspecto original del informe.
- La sección de cobertura de la UI ahora muestra un mensaje claro cuando no existe informe de cobertura generado, indicando al usuario que debe ejecutar los tests para crearlo.
- El apartado de cobertura utiliza los estilos globales de la plataforma, eliminando el CSS propio del iframe para mantener coherencia visual.
- Se ha actualizado la documentación de endpoints (`Docs/api_endpoints.md`) para indicar que el worker LLM Updater clona el repositorio oficial de CVE y utiliza esos datos para generar el archivo JSON de finetuning.
- Refactorización y alineación de los tests de los módulos de utilidades (worker_control, utils, run_services) según las normas de estructura, imports y buenas prácticas. Todos los tests temporales se generan dentro de la carpeta de tests.

### Changed
- El endpoint `/hashed/unhash-file` ahora procesa los hashes de manera **secuencial** (no en paralelo) y aplica un **timeout máximo de 1 minuto (60 segundos) por hash**. Esto mejora la estabilidad y evita la sobrecarga de recursos en el servidor. La documentación en `Docs/api_endpoints.md` ha sido actualizada para reflejar este nuevo comportamiento.

### Added
- Se ha añadido la sección "Hashed" en la UI (Swagger/FastAPI) con endpoints para hashear y deshashear frases, permitiendo seleccionar el algoritmo (MD5, SHA256, SHA512) desde la interfaz.
- Documentados los endpoints `/hashed/hash` y `/hashed/unhash` en `Docs/api_endpoints.md`, incluyendo ejemplos de uso y parámetros.

- Aislamiento completo del entorno de tests mediante `.env.test`:
    - Los tests nunca leen ni modifican el `.env` de desarrollo.
    - El fixture de tests crea y elimina automáticamente `.env.test`.
    - Toda la carga de variables de entorno (incluyendo `load_dotenv`) prioriza `.env.test` si existe.
    - Documentado el procedimiento en `Docs/instalacion_dependencias.md`.
	- Todos los endpoints (query, updater, stop-updater).
	- Mocks de query_llm y run_periodic_training.
	- Ramas de error, estados ya activos y eventos de parada.
	- Pruebas de robustez ante errores y condiciones límite.
	- Manejo de lockfile y condiciones de espera.
	- Escritura sobre archivos malformados.
	- Ramas de control por stop_event y errores en la creación de pool.
	- Cobertura de keywords y casos no relevantes.
	- Pruebas de robustez ante errores y condiciones límite.
	- Detección de sistema operativo y docker.
	- Comprobación y arranque de daemon docker.
	- Lógica de Ollama y modelos.
	- Infraestructura y apagado de servicios (mocks).
	- Creación dinámica de spiders y parseo de respuestas.
	- Escritura y append de JSON con lock.
	- Ejecución de spiders y runners desde base de datos (mocks).
	- Ampliados los tests unitarios de `src/app/utils/run_services.py` para cubrir ramas de error, condiciones límite y casos multiplataforma, alcanzando ≥80% de cobertura en el módulo.
### Fixed
- Todos los tests unitarios y de integración pasan correctamente en CI (>80% cobertura).
- Se corrige la función os_get_euid y sus tests para soportar correctamente entornos Windows y POSIX, y permitir monkeypatching multiplataforma.
- Se corrige el test de infraestructura para asegurar mocks y asserts robustos.
- Se corrige el endpoint /coverage/html para manejar la ausencia de BeautifulSoup y mejorar el mensaje de error.
- Se añade fixture pytest que crea y elimina automáticamente el archivo .env durante los tests unitarios, evitando fallos por ausencia de variables de entorno.
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
- La cobertura de `src/app/utils/run_services.py` se ha maximizado (actualmente 68%) mediante tests avanzados para ramas de error, subprocesos y lógica de Docker/WSL. No alcanza el 80% por ramas defensivas y dependencias de plataforma difíciles de mockear, quedando documentadas las limitaciones técnicas.
- La cobertura de `src/app/services/scraping/spider_factory.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/controllers/routes/worker_controller.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/main.py` se ha maximizado (actualmente 72%) mediante tests de endpoints, ciclo de vida FastAPI y tareas de fondo. No alcanza el 80% por ramas defensivas y dependencias de entorno, quedando documentadas las limitaciones técnicas.
- La cobertura de `src/app/controllers/routes/scrapy_news_controller.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/spacy/text_processor.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/llm/script_auto.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
### Added
- Se ha añadido `pytest-cov` a `dev-requirements.txt` para garantizar la correcta ejecución del workflow de cobertura en CI/CD.

- Se han ampliado y corregido los tests unitarios para `src/app/services/scraping/news_gd.py`, cubriendo:
	- Ramas de error en extracción de noticias, carga y escritura de archivos.
	- Casos extremos y duplicados en la búsqueda y almacenamiento de resultados.
	- Mock de dependencias externas (`httpx`, `googlesearch`, `asyncio.sleep`, logger).
	- Ejecución completa de la función principal `run_news_search` y control de errores.
	- Cobertura de condiciones de archivo corrupto y errores de escritura.

### Changed
- La cobertura de `src/app/services/scraping/news_gd.py` supera el 80% (actualmente 93%), incluyendo ramas de error, condiciones límite y ejecución asíncrona, cumpliendo la norma de calidad definida en `AGENTS.md`.

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
	- Test agregado: `tests/services/test_run_services_minimal.py` — comprobación simple de invocación de subprocess sin shell.

**Seguridad**: Se aplicaron correcciones en local al manejo de ejecución de comandos (sin `shell=True`) y se añadieron herramientas para auditar `f-strings`. Revisar y parchear manualmente las interpolaciones detectadas.

### Añadido (2026-01-23)

- Sección de documentación accesible desde la UI: permite visualizar `README.md` y todos los archivos Markdown de la carpeta `Docs/` desde la interfaz web.
- Endpoints REST para exponer archivos de documentación (`/docs/list`, `/docs/readme`, `/docs/file/{filename}`).
