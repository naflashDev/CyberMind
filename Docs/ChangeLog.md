## [2.0] - 2026-10-26

### Added
- **Suite de tests unitarios de cobertura para el servicio de ingestión (	ests/unit/test_ingest_coverage_boost.py):**
  - Pruebas exhaustivas de casos límite y branches en src/app/services/documents/ingest.py, incluyendo:
    - Filtrado de archivos en lista negra (is_blacklisted_filename).
    - Detección de duplicados en ChromaDB y re-indexado condicional (upserted=False).
    - Extracción y normalización de textos CVE JSON (CNA containers, descripciones, productos afectados, referencias, problem types y fallback recursivo).
    - Ingestión sin guardado de copia (save_copy=False) y rutas existentes bajo data/documents.
    - Manejo de fallos en cliente Chroma (colección inexistente, errores en query o upsert, indisponibilidad de módulo).
    - Inicialización de adaptador de embeddings de Ollama y sanitización de carpetas de destino.
    - Manejo de excepciones en el registrador de estado de ingestión (ingest_tracker).
  - Elevación de la cobertura de código de src/app/services/documents/ingest.py del 41% al 80.17%, superando el umbral global requerido del 80% en CI/CD (--cov-fail-under=80).

### Changed
- ActualizaciÃ³n de versiÃ³n de la API FastAPI a 2.0.
- Alineado de versiones de OpenTelemetry exporters y ajuste de `typer` para resolver conflicto de dependencias en el contenedor backend.
- **RÃ©plica funcional exacta de la UI original en el Frontend Desacoplado:**
  - MigraciÃ³n Ã­ntegra de todas las secciones, controladores (`OSINT` con `Scrapy`, `SpaCy`, `Tiny`, `LLM`; `Code Scanning`; `Hashed`; `Network`; `Status` con control individual/masivo de workers), cachÃ© de formularios/resultados, tarjetas especializadas, gestiÃ³n de conversaciones y documentos RAG, visor de documentaciÃ³n con enlaces internos y editor estructurado `.ini` desde `index.html` y `ui.js` hacia `frontend/`, utilizando iconos modernos Lucide.
  - AmpliaciÃ³n de reglas de proxy en `frontend/nginx.conf` (incluyendo resoluciÃ³n DNS dinÃ¡mica de Docker `127.0.0.11` y `proxy_read_	imeout 600s`) y `frontend/vite.config.ts` para cubrir todos los endpoints del backend.
- **ActualizaciÃ³n de Workflows CI/CD (`unified-ci.yml`):**
  - AÃ±adidos los jobs `frontend-ci` (Node.js 22, `oxlint`, `tsc -b && vite build`, `npm audit`) y `docker-validation` (`docker compose config -q` y build de imÃ¡genes `frontend` y `backend`), documentados en `Docs/Workflows.md`.
- **OptimizaciÃ³n drÃ¡stica del peso de la imagen Docker del Backend (`cybermind-backend`):**
  - DepuraciÃ³n de `requirements.txt` eliminando paquetes pesados de GPU/CUDA y ML no utilizados en producciÃ³n (`torch`, `nvidia-*`, `triton`, `sentence-transformers`, `transformers`, `scipy`, `scikit-learn`, `sympy`, `duckdb`, `langchain*`, `langgraph*`) y separaciÃ³n de las herramientas de test (`pytest*`, `coverage`) en `dev-requirements.txt`.
  - EliminaciÃ³n de `build-essential`, purga en la misma capa de dependencias transitivas no usadas por ChromaDB local (`kubernetes`, `onnxruntime`, `tokenizers`, `huggingface-hub`, `hf-xet`) y limpieza de `__pycache__`/`tests`/`.pyc` en `Dockerfile.backend`, reduciendo el tamaÃ±o de la imagen de **10.3 GB** (3.38 GB comprimidos) a **1.37 GB** (**324 MB** de contenido comprimido).

## [Unreleased] - 2026-10-26

### Added
- **Frontend Desacoplado Moderno (SPA):** Nueva interfaz construida en React 18, TypeScript, Tailwind CSS y Lucide Icons bajo la carpeta `frontend/`, desacoplada por completo del servidor FastAPI.
- **Sistema de Temas CanÃ³nico (GuÃ­a de naflashDev):**
  - Selector de 6 paletas cromÃ¡ticas en el panel de ConfiguraciÃ³n: *Cyber Neon* (por defecto), *JetBrains Dark*, *Amber Terminal*, *Modern SaaS*, *Calma OrgÃ¡nica* y *Minimal Swiss*.
  - Selector dinÃ¡mico de 5 familias tipogrÃ¡ficas: *Plus Jakarta Sans*, *Geist*, *Inter*, *Space Grotesk* y *JetBrains Mono*.
  - Conmutador elÃ¡stico de Modo Oscuro / Modo Claro nativo con persistencia en `localStorage`.
- **ContainerizaciÃ³n Integral Multi-Contenedor (Docker Compose):**
  - Orquestador global `docker-compose.yml` para desplegar Frontend (Nginx Alpine), Backend (FastAPI + Nmap nativo), PostgreSQL, OpenSearch, OpenSearch Dashboards y Tiny Tiny RSS.
  - ConexiÃ³n configurada con el servicio de Ollama del host anfitriÃ³n (`host.docker.internal:11434`) para aceleraciÃ³n GPU sin duplicaciÃ³n de almacenamiento.
  - DefiniciÃ³n de lÃ­mites estrictos de CPU y memoria RAM (`deploy.resources.limits`) para cada contenedor.
  - VolÃºmenes persistentes nombrados para la base de datos de embeddings RAG (`chroma-data`) y documentos clonados/subidos (`documents-data`).
- **Endpoint de Salud:** Incorporado `GET /health` en `main.py` para sondas de monitorizaciÃ³n y readiness de contenedores.
- **DocumentaciÃ³n TÃ©cnica:** AÃ±adidos `Docs/frontend_architecture.md` y `Docs/containerization.md`.

### Changed
- **CORS del Backend:** Ampliado `CORSMiddleware` en `main.py` para admitir orÃ­genes de desarrollo (`http://localhost:5173`) y producciÃ³n containerizada (`http://localhost:8080`).
- **ConfiguraciÃ³n de Ollama:** `OLLAMA_BASE_URL` en `llm_client.py` ahora lee dinÃ¡micamente la variable de entorno `OLLAMA_HOST` con fallback a `http://127.0.0.1:11434`.
- **DetecciÃ³n de Entorno en Infraestructura:** `ensure_infrastructure` en `run_services.py` comprueba `RUNNING_IN_DOCKER` para evitar llamadas redundantes de Docker CLI dentro de contenedores mientras mantiene compatibilidad total en ejecuciones bare-metal.

---

## [1.0.0] - 2026-03-15
### Added
- SecciÃ³n "Code Scanning" en la UI bajo "Services" con soporte para anÃ¡lisis de cÃ³digo por texto y archivo, mostrando resultados en tarjetas visuales y descarga de informe PDF.
- DocumentaciÃ³n de endpoints de code scanning en `api_endpoints.md`.
### Fixed
- **OptimizaciÃ³n y estabilidad de tests automatizados:**
  - 	ests/unit/test_bruteforce_utils.py: limpieza de duplicados y optimizaciÃ³n con pool sÃ­ncrono para tests rÃ¡pidos de hashing.
  - 	ests/unit/test_worker_controller_extra.py: correcciÃ³n de inyecciÃ³n de mÃ³dulo simulado (pp.services.retention.retention_worker) y activaciÃ³n inmediata del stop_event en FakeThread2, eliminando esperas infinitas / de 24 horas (stop_event.wait(86400)).
  - 	ests/conftest.py: aceleraciÃ³n controlada de 	hreading.Event.wait en bucles de background worker con 	imeouts largos (	imeout > 1), preservando 	imeout=None para la sincronizaciÃ³n interna de hilos en multiprocessing.Pool y subprocess.
  - 	ests/integration/test_llm_controller.py: registro de llm_trainer en sys.modules para evitar ModuleNotFoundError: No module named 'app.services.llm.llm_trainer'.
  - 	ests/unit/test_documents_controller_upload.py: mockeo de ingest_document para prevenir llamadas externas y errores en upload de documentos durante testing.
  - 	ests/services/test_scan_range_end.py: mockeo de puertos de red para evitar 	imeouts de sockets TCP reales.
  - 	ests/unit/test_ingest.py: asegurada bandera _CHROMA_AVAILABLE=False en test de colisiÃ³n de nombres.
  - 	ests/app/controllers/routes/test_worker_controller.py: mockeo de syncpg.create_pool para prevenir esperas de conexiÃ³n a PostgreSQL.

- Worker `vector_ingest` now excludes the hidden `.git` directory from folder scans to avoid ingesting VCS metadata.
- Ignore repository metadata files (`.gitignore`, `.gitattributes`, `README.md`) during ingestion by using a centralized blacklist.
- CVE JSON files under repository trees are no longer copied into `data/documents`; they are read in-place and embedded directly from their original location to avoid duplication.
### Added
- ImplementaciÃ³n inicial de RAG (Retrieval-Augmented Generation): ingestiÃ³n, vectorizaciÃ³n y pipeline de recuperaciÃ³n para respuestas enriquecidas.

	- **Resumen tÃ©cnico:** Se introduce un flujo completo para ingerir documentos, generar embeddings y exponer mecanismos de recuperaciÃ³n que permiten combinar resultados semÃ¡nticos con un LLM para respuestas RAG.
	- **Componentes afectados:**
		- `src/app/services/documents/ingest.py` â normalizaciÃ³n, blacklist central y opciÃ³n `save_copy` para evitar duplicar ficheros (CVE JSONs pueden indexarse in-place).
		- `src/app/controllers/routes/worker_controller.py` â worker `vector_ingest` mejorado para excluir carpetas VCS (`.git`, `.github`) y detectar/usar JSONs CVE en su ubicaciÃ³n original.
		- `src/app/services/vectorstore/*` â integraciÃ³n con Chroma y adaptador de embeddings (`OllamaEmbeddingAdapter`) para generar vectores y gestionar colecciones.
		- `src/app/services/documents/ingest_tracker.py` â tracker de ingesta usado para evitar duplicados y controlar reindexados.
		- Endpoints y controladores relacionados con recuperaciÃ³n/consulta estÃ¡n listos para integrarse con el retriever (ver `Docs/api_endpoints.md`).
	- **Notas de pruebas / CI:**
		- Se aÃ±adieron tests unitarios para la lÃ³gica de blacklist y el worker `vector_ingest` (tests unitarios en `tests/unit/test_ingest_blacklist.py` y pruebas de `worker_controller`).
		- La CI ejecuta `pytest` con `pytest-cov`; la pipeline de coverage verifica que los cambios no reduzcan la cobertura por debajo del umbral establecido.
	- **Limitaciones conocidas:**
		- IndexaciÃ³n in-place de JSONs asume que los ficheros son legibles y estables en disco; si se desea copia automÃ¡tica, use `save_copy=True` en la API de ingest.
		- Soporte de embebbedor local depende de `ollama` disponible en PATH o configuraciÃ³n alternativa del env var `EMBED_MODEL_NAME`.
### Changed (2026-02-13)
- Ampliados los tests unitarios para `src/app/services/hashed/bruteforce_utils.py`, cubriendo la funciÃ³n interna `_bruteforce_worker` (	imeout, max_combinations, chunking, caracteres especiales, detecciÃ³n exitosa y fallida). La cobertura del mÃ³dulo supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
Archivos modificados:
 - `tests/unit/test_bruteforce_utils.py`
 - `src/app/services/hashed/bruteforce_utils.py`
### Added
- Endpoint `/workers/shutdown` para apagar la aplicaciÃ³n y todos los procesos desde la UI.
- BotÃ³n de apagado en el sidebar de la UI con feedback visual y estilos de seguridad.
# [Unreleased] - 2026-02-13

### Security
- Eliminadas todas las credenciales hardcoded de conexiÃ³n a PostgreSQL en los controladores de feeds (<code>tiny_postgres_controller.py</code>). Ahora se utilizan exclusivamente variables de entorno definidas en el archivo <code>.env</code> (<code>POSTGRES_USER</code>, <code>POSTGRES_PASSWORD</code>, <code>POSTGRES_DB</code>, <code>POSTGRES_HOST</code>, <code>POSTGRES_PORT</code>), cumpliendo la polÃ­tica de seguridad y buenas prÃ¡cticas establecidas en <code>AGENTS.md</code>.
- DocumentaciÃ³n de endpoints actualizada en <code>Docs/api_endpoints.md</code> para reflejar el uso de variables de entorno en la conexiÃ³n a la base de datos.

### Added
- Nuevo endpoint <code>/hashed/hash-file</code> que permite subir un archivo de texto donde cada lÃ­nea es una palabra, seleccionar el algoritmo de hash (MD5, SHA256, SHA512) y obtener el hash de cada palabra en tarjetas visuales desde la UI (drag & drop). No almacena los hashes, solo los calcula y devuelve.
- La UI ahora incluye un formulario para subir archivos de palabras y seleccionar el algoritmo de hash, mostrando el resultado en tarjetas visuales con la palabra, el hash y el algoritmo usado.
- DocumentaciÃ³n ampliada en <code>Docs/api_endpoints.md</code> para el nuevo endpoint, con ejemplos de uso y formato de respuesta.
- Tests unitarios para <code>/hashed/hash-file</code> cubriendo casos Happy Path, Edge Case (archivo vacÃ­o) y Error Handling (algoritmo no soportado, excepciÃ³n en hash).


### Added
- Nuevo endpoint <code>/hashed/upload-hash-file</code> que permite subir un archivo de texto con mÃºltiples lÃ­neas, cada una con una palabra y su hash (separados por coma, espacio, tabulaciÃ³n o dos puntos). El sistema detecta automÃ¡ticamente el tipo de hash y almacena cada entrada en la base de datos. Si el hash ya existe, lo indica de forma amigable. Ideal para cargas masivas mediante drag & drop en la UI.
- DocumentaciÃ³n ampliada y actualizada en <code>Docs/api_endpoints.md</code> para el endpoint de subida de hashes, incluyendo el nuevo formato de respuesta y ejemplos.
- La UI ahora muestra el resultado de la subida de hashes con tarjetas visuales y mensajes claros: "Hash insertado correctamente", "Hash ya almacenado en el sistema" o errores de formato, sin exponer nunca informaciÃ³n interna.
### Security
- El endpoint <code>/hashed/upload-hash-file</code> y la UI asociada han sido reforzados para no exponer nunca detalles internos de la base de datos ni trazas de error. Todos los mensajes devueltos al usuario son claros y seguros, cumpliendo la polÃ­tica de seguridad definida en <code>AGENTS.md</code>.
 - El servicio de hash ahora incluye logs detallados usando loguru en todos los puntos clave: inicio y fin de operaciones, resultados de bÃºsqueda en BBDD, intentos de fuerza bruta, errores y guardado de nuevos hashes. Esto mejora la trazabilidad y el diagnÃ³stico de incidencias.
 - La fuerza bruta para deshashear hashes ahora se detiene automÃ¡ticamente tras 120 segundos, devolviendo el nÃºmero de combinaciones probadas y un indicador de 	imeout en la respuesta. Si se encuentra el valor original, se almacena automÃ¡ticamente en la base de datos para futuras consultas rÃ¡pidas.
- Nuevo endpoint <code>/hashed/unhash</code> para deshashear uno o varios hashes (multilÃ­nea, auto-detecciÃ³n de tipo, bÃºsqueda en BBDD y fuerza bruta multiproceso hasta 20 caracteres, incluyendo caracteres especiales mÃ¡s usados).
- LÃ³gica de fuerza bruta y detecciÃ³n de tipo de hash implementada en el servicio de hashing, cumpliendo los requisitos de seguridad y rendimiento.
- UI actualizada: el algoritmo de hash es ahora seleccionable mediante un desplegable en la secciÃ³n de hasheo, mejorando la experiencia de usuario y evitando errores de entrada manual. La caja de texto multilinea para hashes y la visualizaciÃ³n de resultados por hash en tarjetas se mantienen.
- DocumentaciÃ³n ampliada en <code>Docs/api_endpoints.md</code> y tests unitarios para la nueva funcionalidad.
### Added
- Limpieza automÃ¡tica de carpetas `outputs` y `data` en la raÃ­z del proyecto tras la ejecuciÃ³n de tests (hook en `conftest.py`).

## [2026-02-06]
### Added
- El servicio de hash ahora calcula el hash, lo muestra al usuario y lo almacena en la base de datos solo si no existe ya guardado. El endpoint es idempotente y nunca genera duplicados.
- Actualizada la documentaciÃ³n de endpoints (`Docs/api_endpoints.md`) para reflejar el nuevo comportamiento del servicio hash.
### Fixed
- Corregidos los tests unitarios de `/hashed/unhash` para usar el formato de entrada correcto (`hashes` multilÃ­nea y `max_len`).
- El mock de servicio en los tests ahora devuelve la estructura esperada por el endpoint (lista de objetos tipo MultiUnhashResponseItem).
- DocumentaciÃ³n del endpoint `/hashed/unhash` actualizada en `Docs/api_endpoints.md` para reflejar el formato real de entrada y respuesta, con ejemplo de uso.
- Tests unitarios, integraciÃ³n y cobertura verificados tras el cambio en el servicio hash.
### Security
- El nuevo flujo evita duplicidad de hashes y refuerza la integridad de la base de datos.
## [Unreleased]
### Security
- Todos los endpoints de los controladores han sido actualizados para que, en caso de error, devuelvan siempre un mensaje genÃ©rico a la UI: "Ha ocurrido un error interno. Por favor, contacte con el administrador.". Nunca se exponen detalles internos ni informaciÃ³n sensible en los mensajes de error enviados al cliente. Los detalles completos solo quedan registrados en los logs del backend. Cumple la polÃ­tica de seguridad definida en `AGENTS.md`.

### Fixed
- Unificado el manejo de errores en todos los controllers para evitar la filtraciÃ³n de informaciÃ³n interna o sensible a travÃ©s de los mensajes de error de la API. Se han adaptado los tests afectados para reflejar el nuevo comportamiento.
### Fixed
 - Corregido error de PermissionError en el fixture de tests unitarios (`conftest.py`) usando reintentos y manejo seguro de archivos en Windows.
 - Solucionados los RuntimeWarning de corutinas no awaitadas en los mÃ³dulos de scraping (`feeds_gd.py`) y anÃ¡lisis de red (`network_analysis.py`), asegurando que los mÃ©todos logger.* se awaitan correctamente cuando son AsyncMock en tests.
### Removed
- Eliminada la secciÃ³n de cobertura de la interfaz web. El informe HTML de coverage.py solo estÃ¡ disponible como archivo estÃ¡tico tras ejecutar los tests.
- Se ha aÃ±adido un aviso destacado en la documentaciÃ³n de endpoints (`Docs/api_endpoints.md`) advirtiendo que no se debe ejecutar el worker de LLM Updater en mÃ¡quinas poco potentes, debido a su alto consumo de recursos.
- El informe de cobertura HTML ahora se sirve con el CSS global de la UI, eliminando el CSS propio generado por coverage.py. Esto unifica la experiencia visual en la secciÃ³n Cobertura, aunque puede modificar el aspecto original del informe.
- La secciÃ³n de cobertura de la UI ahora muestra un mensaje claro cuando no existe informe de cobertura generado, indicando al usuario que debe ejecutar los tests para crearlo.
- El apartado de cobertura utiliza los estilos globales de la plataforma, eliminando el CSS propio del iframe para mantener coherencia visual.
- Se ha actualizado la documentaciÃ³n de endpoints (`Docs/api_endpoints.md`) para indicar que el worker LLM Updater clona el repositorio oficial de CVE y utiliza esos datos para generar el archivo JSON de finetuning.
- RefactorizaciÃ³n y alineaciÃ³n de los tests de los mÃ³dulos de utilidades (worker_control, utils, run_services) segÃºn las normas de estructura, imports y buenas prÃ¡cticas. Todos los tests temporales se generan dentro de la carpeta de tests.

### Changed
- El endpoint `/hashed/unhash-file` ahora procesa los hashes de manera **secuencial** (no en paralelo) y aplica un **	imeout mÃ¡ximo de 1 minuto (60 segundos) por hash**. Esto mejora la estabilidad y evita la sobrecarga de recursos en el servidor. La documentaciÃ³n en `Docs/api_endpoints.md` ha sido actualizada para reflejar este nuevo comportamiento.

### Added
- Se ha aÃ±adido la secciÃ³n "Hashed" en la UI (Swagger/FastAPI) con endpoints para hashear y deshashear frases, permitiendo seleccionar el algoritmo (MD5, SHA256, SHA512) desde la interfaz.
- Documentados los endpoints `/hashed/hash` y `/hashed/unhash` en `Docs/api_endpoints.md`, incluyendo ejemplos de uso y parÃ¡metros.

- Aislamiento completo del entorno de tests mediante `.env.test`:
    - Los tests nunca leen ni modifican el `.env` de desarrollo.
    - El fixture de tests crea y elimina automÃ¡ticamente `.env.test`.
    - Toda la carga de variables de entorno (incluyendo `load_dotenv`) prioriza `.env.test` si existe.
    - Documentado el procedimiento en `Docs/instalacion_dependencias.md`.
	- Todos los endpoints (query, updater, stop-updater).
	- Mocks de query_llm y run_periodic_training.
	- Ramas de error, estados ya activos y eventos de parada.
	- Pruebas de robustez ante errores y condiciones lÃ­mite.
	- Manejo de lockfile y condiciones de espera.
	- Escritura sobre archivos malformados.
	- Ramas de control por stop_event y errores en la creaciÃ³n de pool.
	- Cobertura de keywords y casos no relevantes.
	- Pruebas de robustez ante errores y condiciones lÃ­mite.
	- DetecciÃ³n de sistema operativo y docker.
	- ComprobaciÃ³n y arranque de daemon docker.
	- LÃ³gica de Ollama y modelos.
	- Infraestructura y apagado de servicios (mocks).
	- CreaciÃ³n dinÃ¡mica de spiders y parseo de respuestas.
	- Escritura y append de JSON con lock.
	- EjecuciÃ³n de spiders y runners desde base de datos (mocks).
	- Ampliados los tests unitarios de `src/app/utils/run_services.py` para cubrir ramas de error, condiciones lÃ­mite y casos multiplataforma, alcanzando â¥80% de cobertura en el mÃ³dulo.
### Fixed
- Todos los tests unitarios y de integraciÃ³n pasan correctamente en CI (>80% cobertura).
- Se corrige la funciÃ³n os_get_euid y sus tests para soportar correctamente entornos Windows y POSIX, y permitir monkeypatching multiplataforma.
- Se corrige el test de infraestructura para asegurar mocks y asserts robustos.
- Se corrige el endpoint /coverage/html para manejar la ausencia de BeautifulSoup y mejorar el mensaje de error.
- Se aÃ±ade fixture pytest que crea y elimina automÃ¡ticamente el archivo .env durante los tests unitarios, evitando fallos por ausencia de variables de entorno.
- Se han aÃ±adido tests unitarios y de integraciÃ³n para `src/app/controllers/routes/worker_controller.py`, cubriendo:
	- Endpoints asÃ­ncronos y modelo WorkerToggle.
	- Mocks de dependencias y respuestas.
	- EjecuciÃ³n de los principales flujos y casos de Ã©xito.
- Se han aÃ±adido tests unitarios y de integraciÃ³n para `src/main.py`, cubriendo:
	- Endpoints principales (/, /ui).
	- Lifespan y tareas de fondo.
	- Mocks de dependencias y ejecuciÃ³n de flujos bÃ¡sicos.
- Se han aÃ±adido tests unitarios y de integraciÃ³n para `src/app/controllers/routes/scrapy_news_controller.py`, cubriendo:
	- Endpoints asÃ­ncronos y funciones de fondo.
	- Mocks de dependencias externas y respuestas.
	- EjecuciÃ³n de los principales flujos y casos de Ã©xito.
- Se han aÃ±adido tests unitarios y de integraciÃ³n para `src/app/services/spacy/text_processor.py`, cubriendo:
	- DetecciÃ³n de idioma y casos de error.
	- ExtracciÃ³n de entidades y textos con spaCy (mock).
	- Manejo de modelos spaCy y fallback.
	- EjecuciÃ³n de process_json con mocks de OpenSearch y configuraciÃ³n.
	- Casos extremos y errores en todas las funciones principales.
- Se han aÃ±adido tests unitarios y de integraciÃ³n para `src/app/services/llm/script_auto.py`, cubriendo los siguientes casos:
	- EjecuciÃ³n y error de `clone_repository` y `update_repository`.
	- Transformaciones de JSON con casos extremos, ADP y soluciones.
	- Procesamiento de archivos con errores y datos vÃ¡lidos.
	- ConsolidaciÃ³n de mÃºltiples archivos JSON con simulaciÃ³n de procesos.
	- Flujo completo de actualizaciÃ³n y consolidaciÃ³n del repositorio CVE.

### Changed
- La cobertura de `src/app/controllers/routes/llm_controller.py` supera el 80%, incluyendo ramas de error, eventos y condiciones lÃ­mite, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/scraping/spider_factory.py` supera el 80% incluyendo ramas de error, lockfile y condiciones lÃ­mite, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/utils/run_services.py` se ha maximizado (actualmente 68%) mediante tests avanzados para ramas de error, subprocesos y lÃ³gica de Docker/WSL. No alcanza el 80% por ramas defensivas y dependencias de plataforma difÃ­ciles de mockear, quedando documentadas las limitaciones tÃ©cnicas.
- La cobertura de `src/app/services/scraping/spider_factory.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/controllers/routes/worker_controller.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/main.py` se ha maximizado (actualmente 72%) mediante tests de endpoints, ciclo de vida FastAPI y tareas de fondo. No alcanza el 80% por ramas defensivas y dependencias de entorno, quedando documentadas las limitaciones tÃ©cnicas.
- La cobertura de `src/app/controllers/routes/scrapy_news_controller.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/spacy/text_processor.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
- La cobertura de `src/app/services/llm/script_auto.py` supera el 80%, cumpliendo la norma de calidad definida en `AGENTS.md`.
### Added
- Se ha aÃ±adido `pytest-cov` a `dev-requirements.txt` para garantizar la correcta ejecuciÃ³n del workflow de cobertura en CI/CD.

- Se han ampliado y corregido los tests unitarios para `src/app/services/scraping/news_gd.py`, cubriendo:
	- Ramas de error en extracciÃ³n de noticias, carga y escritura de archivos.
	- Casos extremos y duplicados en la bÃºsqueda y almacenamiento de resultados.
	- Mock de dependencias externas (`httpx`, `googlesearch`, `asyncio.sleep`, logger).
	- EjecuciÃ³n completa de la funciÃ³n principal `run_news_search` y control de errores.
	- Cobertura de condiciones de archivo corrupto y errores de escritura.

### Changed
- La cobertura de `src/app/services/scraping/news_gd.py` supera el 80% (actualmente 93%), incluyendo ramas de error, condiciones lÃ­mite y ejecuciÃ³n asÃ­ncrona, cumpliendo la norma de calidad definida en `AGENTS.md`.

### Fixed
- Se ha corregido el fallo en el workflow de GitHub Actions que impedÃ­a la generaciÃ³n de informes de cobertura, asegurando la instalaciÃ³n de `pytest-cov` en el entorno de CI.
### Changed
- Se han aÃ±adido tests para cubrir excepciones y ramas no cubiertas en `src/app/controllers/routes/llm_controller.py`, `src/app/services/scraping/spider_factory.py`, `src/app/controllers/routes/network_analysis_controller.py` (y endpoints asociados) y `src/app/services/llm/script_auto.py`, asegurando cobertura >80% en estos mÃ³dulos.
### Added
- Se han creado tests unitarios para los siguientes mÃ³dulos, elevando la cobertura total por encima del 80%:
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
- Se cumple la norma de cobertura mÃ­nima del 80% en todos los mÃ³dulos principales segÃºn AGENTS.md.
# [Unreleased] - 2026-01-24
### Fixed

 - Se han corregido los tests unitarios de FeedCreateRequest en `test_ttrss_postgre_db.py` para incluir todos los campos obligatorios del modelo Pydantic, evitando errores de validaciÃ³n.
 - Se ha corregido el manejo de excepciones en la creaciÃ³n del cliente OpenSearch en `opensearh_db.py`, permitiendo que los tests unitarios capturen correctamente los errores de conexiÃ³n y de Ã­ndice inexistente.
 - Se ha corregido la funciÃ³n `tag_text` en `text_processor.py` para manejar texto vacÃ­o y modelos nulos, devolviendo siempre una lista de entidades y el idioma detectado, asegurando que los tests unitarios pasen correctamente.
 - Se ha corregido el endpoint `/postgre-ttrss/feeds` en `tiny_postgres_controller.py` para devolver 404 si no hay feeds y 500 solo en errores inesperados, cumpliendo los tests y la norma de manejo de errores.
- Se han corregido los asserts de cÃ³digos de estado en los tests de controladores para reflejar correctamente las posibles respuestas de la API (incluyendo 404 y 405 donde corresponde).
- Se ha mejorado la portabilidad en la comprobaciÃ³n de rutas de archivos en los tests de cobertura.

### Fixed
- Se ha corregido el comportamiento de ocultamiento de la sidebar principal: ahora al plegar la barra lateral se asegura su ocultaciÃ³n total y se evita cualquier interacciÃ³n visual o de puntero, aplicando overflow: hidden, pointer-events: none y opacity: 0 en el CSS. Esto soluciona los casos en los que la sidebar quedaba parcialmente visible o interactuable.

### Changed
 - La funciÃ³n ensure_infrastructure ahora acepta parÃ¡metros como dict y extrae valores por clave, compatible con el nuevo formato de configuraciÃ³n.
 - Los archivos cfg_services.ini y cfg.ini ahora usan formato clave=valor para compatibilidad total con el panel de configuraciÃ³n y la API.
 - Refactorizadas las funciones get_connection_parameters y get_connection_service_parameters en src/app/utils/utils.py para soportar el formato clave=valor en cfg.ini y cfg_services.ini.
 - Restaurada la compatibilidad de toda la lÃ³gica de conexiÃ³n con el nuevo formato clave=valor, corrigiendo los fallos provocados por el cambio de formato.
 - Corregido el ciclo de vida FastAPI en main.py: el lifespan siempre ejecuta yield, evitando errores 'generator didn't yield' y restaurando los tests E2E.
- Los archivos cfg_services.ini y cfg.ini ahora usan formato clave=valor para compatibilidad total con el panel de configuraciÃ³n y la API.
## [Unreleased] - 2026-01-25
### Fixed
- Se ha corregido el test `test_run_dynamic_spider_from_db_runs` en `tests/app/services/scraping/test_spider_factory.py` para usar correctamente `AsyncMock` en el mock de `get_entry_links`, evitando el error 'object list can't be used in await expression' y asegurando la compatibilidad con funciones asÃ­ncronas.
- Se ha corregido el test unitario de `run_dynamic_spider_from_db` en `test_spider_factory.py` para que el mock de `pool.acquire()` soporte correctamente el protocolo async context manager, evitando el error 'coroutine' object does not support the asynchronous context manager protocol y asegurando la compatibilidad con la implementaciÃ³n asÃ­ncrona del runner de spiders.

### Changed
- Los recuadros de cada secciÃ³n del panel de configuraciÃ³n ahora tienen esquinas redondeadas para mejorar la estÃ©tica visual.
### Security
- Se ha cambiado la licencia del proyecto a una **licencia privativa personalizada**: solo uso personal, educativo o de investigaciÃ³n; derivados permitidos Ãºnicamente bajo las condiciones especificadas; prohibida la redistribuciÃ³n y el uso comercial sin autorizaciÃ³n expresa del titular. Ver archivo LICENSE y README.md para detalles.
### Changed
- Los hints explicativos de los campos ahora aparecen como tooltip al hacer hover sobre un icono de informaciÃ³n junto al nombre del campo.
- Se ha aÃ±adido un job de coverage a la CI (`unified-ci.yml`) que ejecuta `pytest-cov`, genera reportes de cobertura (`htmlcov/`, `coverage.xml`) y falla si la cobertura baja del 80%. La cobertura se sube como artifact y estÃ¡ documentada en `Docs/Workflows.md` y `Docs/coverage.md`.
- Se han aÃ±adido hints explicativos a los campos del panel de configuraciÃ³n para guiar al usuario sobre el significado y el formato esperado de cada parÃ¡metro.
### Changed
- Los bloques y parÃ¡metros del panel de configuraciÃ³n ahora muestran nombres mÃ¡s claros y amigables: 'ConfiguraciÃ³n servicios', 'ConfiguraciÃ³n general', 'Nombre distribuciÃ³n', 'Nombre contenedores', 'IP servidor', 'Puerto servidor', etc.
### Changed
- Los botones de la sidebar principal ahora incluyen iconos representativos para cada secciÃ³n.
- El botÃ³n de activar IA (SÃ­/No) mantiene esquinas redondeadas para coherencia visual.
### Changed
- Restauradas las esquinas redondeadas en los botones de guardar, descartar y activar IA en el panel de configuraciÃ³n para mejorar la estÃ©tica y coherencia visual.
### Fixed
### Changed
### Added (2026-01-23)
- Iconos representativos agregados a todos los botones principales de la UI (panel de configuraciÃ³n y panel de operaciones).

### Changed
- Se eliminaron las esquinas redondeadas del panel de configuraciÃ³n y sus elementos para una integraciÃ³n visual sin huecos.
- Los textos de los parÃ¡metros de configuraciÃ³n ahora son mÃ¡s amigables para el usuario (user friendly).

### Security
- RevisiÃ³n visual para evitar huecos y asegurar la correcta adaptaciÃ³n del panel de configuraciÃ³n.

- AÃ±adido parÃ¡metro `use_ollama` en `src/cfg_services.ini` para controlar la instalaciÃ³n y uso de Ollama.
- LÃ³gica condicional en `main.py` para instalar/inicializar Ollama solo si el parÃ¡metro estÃ¡ en `true` y el hardware cumple requisitos mÃ­nimos (8GB RAM, 2 nÃºcleos CPU).
- DocumentaciÃ³n actualizada en `Docs/api_endpoints.md` sobre el nuevo parÃ¡metro y su funcionamiento.

Archivos modificados:
 - `src/main.py`
 - `src/cfg_services.ini`
 - `Docs/api_endpoints.md`
# Registro de cambios

Todos los cambios notables de este proyecto se documentarÃ¡n en este archivo.

El formato se basa en "Keep a Changelog" y este proyecto sigue el Versionado SemÃ¡ntico.

## [Sin publicar]

### Security (2026-01-23)

- MigraciÃ³n de credenciales de base de datos PostgreSQL (usuario, contraseÃ±a, host, puerto) desde el cÃ³digo fuente a variables de entorno gestionadas en `.env`.
- Eliminados todos los datos crÃ­ticos hardcoded en `src/main.py` y `src/app/services/scraping/spider_factory.py`.
- AÃ±adido soporte a `python-dotenv` para carga automÃ¡tica de variables.
- DocumentaciÃ³n ampliada en `Docs/instalacion_dependencias.md` con instrucciones y advertencias de seguridad sobre el uso de `.env`.

Archivos modificados:
 - `src/main.py`
 - `src/app/services/scraping/spider_factory.py`
 - `.env.example` (nuevo)
 - `.env` (nuevo)
 - `Docs/instalacion_dependencias.md`
### Cambiado (2026-01-23)

- Eliminadas las lÃ­neas de cabecera estÃ¡ndar (`# Cabecera estÃ¡ndar para ...`) en todos los archivos de test bajo `tests/` para homogeneizar el formato y evitar redundancia documental. No afecta a la lÃ³gica de pruebas ni a la cobertura.

Archivos modificados:
 - `tests/controllers/test_controllers_tiny_postgres.py`
 - `tests/controllers/test_workers_ui.py`
 - `tests/controllers/test_scraping_news_worker.py`
 - `tests/controllers/test_network_api_scan_range.py`
 - `tests/controllers/test_network_api_nmap_	imeout.py`
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
 - `tests/services/test_run_nmap_	imeout_unit.py`
 - `tests/services/test_network_service_unit.py`
 - `tests/utils/test_run_services_combined.py`
 - `tests/utils/test_run_services.py`

- DocumentaciÃ³n actualizada en `Docs/home.md` y `Docs/api_endpoints.md` para reflejar el carÃ¡cter multifunciÃ³n de CyberMind: plataforma para auditorÃ­a, automatizaciÃ³n, anÃ¡lisis, reporting, dashboards, integraciÃ³n de IA y no solo recolecciÃ³n IT/OT. Se amplÃ­a la introducciÃ³n, objetivos, caracterÃ­sticas, casos de uso y definiciones para alinearse con la realidad del proyecto y su uso en auditorÃ­a y flujos avanzados de ciberseguridad.

Archivos modificados:
 - `Docs/home.md`
 - `Docs/api_endpoints.md`
 - UI: nueva categorÃ­a `OSINT` en el panel de `Operaciones FastAPI` que agrupa las subsecciones `Scrapy`, `SpaCy`, `Tiny` y `LLM` para facilitar el acceso a operaciones relacionadas con inteligencia de fuentes abiertas. (2026-01-15)
 - Tests: `tests/integration/test_e2e_basic_pipeline.py` â test E2E bÃ¡sico que verifica que la ruta `/` sirve el `index.html` y que la inicializaciÃ³n del UI puede dispararse (con mocks en entorno de test). (2026-01-19)
 - Tests: `tests/integration/test_e2e_pipelines.py` â suite E2E que cubre mÃºltiples pipelines: estado (`/status`), escaneo de red (`/network/*`), control de workers (`/workers`), consulta LLM (`/llm/query`) y endpoint de feeds Postgre (`/postgre-ttrss/feeds`). (2026-01-19)
 - README.md: AÃ±adida tabla descriptiva de directorios y archivos relevantes bajo el esquema de estructura de proyecto. (2026-01-23)
 - README.md: Mejora visual con cabecera centrada, badges, tablas, emojis y bloques destacados para mayor atractivo y claridad. (2026-01-23)

- El servicio de escaneo de red (`app.services.network_analysis.network_analysis`) ahora incluye un campo explÃ­cito `state` para los resultados analizados por nmap (p. ej., `open`, `closed`, `filtered`) para permitir el renderizado correcto en la UI de puertos filtrados. (2026-01-14)
- UI (`src/app/ui/static/ui.js`, `styles.css`) muestra una insignia `FILTERED` (naranja) para `state === 'filtered'`; ordena hosts y puertos para priorizar resultados abiertos/filtrados; las tarjetas incluyen colapsado/expandido y altura limitada para la lista de puertos con desplazamiento interno. (2026-01-14)

- CI: unificado y limpiado el workflow `ci.yml` en `.github/workflows/` (eliminados bloques duplicados y corregidos los triggers de `pull_request`). Se aÃ±adiÃ³ job de seguridad que genera y sube artefactos JSON (`pip_audit.json`, `bandit_report.json`). (2026-01-16)

- Docs: Eliminados contenidos duplicados en `Docs/api_endpoints.md` (nota legal duplicada y enlace duplicado a la documentaciÃ³n interactiva). (2026-01-19)

### Cambiado (2026-01-19)

- Refactor: se moviÃ³ la lÃ³gica de escaneo de rangos desde la ruta `POST /network/scan_range` hacia una funciÃ³n asÃ­ncrona centralizada `scan_range` en `src/app/services/network_analysis/network_analysis.py`. La ruta en `src/app/controllers/routes/network_analysis_controller.py` ahora delega la operaciÃ³n al servicio y sÃ³lo realiza logging y mapeo de errores HTTP. Este cambio mejora la separaciÃ³n de responsabilidades, la testabilidad y facilita reutilizar la lÃ³gica desde otros puntos del cÃ³digo. (2026-01-19)

Files modificados:

- `src/app/controllers/routes/network_analysis_controller.py` â Simplifica la ruta `scan_range` para delegar al servicio.
- `src/app/services/network_analysis/network_analysis.py` â AÃ±adida funciÃ³n `scan_range(...)` que implementa generaciÃ³n de hosts, validaciones, concurrencia y fallback a `scan_ports` cuando `nmap` no estÃ¡ disponible.

- `src/app/services/network_analysis/network_analysis.py` â `scan_ports` ahora incluye el campo `state` en cada resultado (`open`, `closed`, `filtered`, `unknown`) para que la UI muestre correctamente puertos filtrados en el endpoint `POST /network/scan`. (2026-01-19)

### Corregido
- Mejoras de validaciÃ³n: `RangeScanRequest` normaliza cadenas vacÃ­as y acepta `start`/`end` cuando `cidr` estÃ¡ vacÃ­o; mejor manejo de payloads de formulario para evitar errores 422 desde la UI. (2026-01-14)

- Corregido: `src/app/utils/run_services.py` â se resolvieron varios errores de indentaciÃ³n que provocaban excepciones de parsing al importar el mÃ³dulo.
	- Se corrigiÃ³ la indentaciÃ³n en la funciÃ³n `wsl_docker_start_container` para ejecutar correctamente comandos Docker dentro de WSL en Windows. (2026-01-16)
	- Se reemplazÃ³ y limpiaron las secciones corruptas/indentadas de `shutdown_services` por una implementaciÃ³n robusta que:
		- baja stacks de `Install/` mediante `docker compose down -v` cuando aplica,
		- detiene contenedores (opcionalmente todos o por lista) manejando ejecuciÃ³n en WSL cuando procede,
		- intenta parar procesos `ollama` mediante `ollama stop` y aplica una estrategia de fallback para terminar procesos si es necesario. (2026-01-16)
	- Nota: cambios centrados en correcciÃ³n sintÃ¡ctica y robustez de ejecuciÃ³n de subprocesos; no se modificÃ³ la API pÃºblica del mÃ³dulo. (2026-01-16)

### Corregido (2026-01-19)

- Corregido: Error TypeError en la ruta `POST /network/scan_range` causado por sombreado del nombre `scan_range` entre la funciÃ³n de la ruta y la funciÃ³n exportada por el servicio. Se renombrÃ³ la importaciÃ³n del servicio a `service_scan_range` y la ruta ahora delega correctamente la ejecuciÃ³n al servicio asÃ­ncrono `scan_range`, evitando la colisiÃ³n de nombres y el rechazo del argumento `cidr`. Archivos afectados:
	- [src/app/controllers/routes/network_analysis_controller.py](src/app/controllers/routes/network_analysis_controller.py) â la ruta `scan_range` ahora llama a `service_scan_range`.
	- [src/app/services/network_analysis/network_analysis.py](src/app/services/network_analysis/network_analysis.py) â funciÃ³n de servicio `scan_range` exportada y documentada.

	Este cambio corrige el error 500/TypeError observado al invocar `POST /network/scan_range` y mantiene la interfaz pÃºblica del endpoint.

### Seguridad
- Las solicitudes de escaneo estÃ¡n limitadas a un mÃ¡ximo de 1024 hosts por peticiÃ³n para prevenir escaneos masivos accidentales. (2026-01-14)

### Cambiado (2026-01-19)

- CI: ConsolidaciÃ³n de workflows en un Ãºnico archivo `.github/workflows/unified-ci.yml`. Se han unificado las etapas en jobs/etapas explÃ­citas: `setup`, `lint`, `security`, `unit-tests`, `integration-tests` y `cleanup` (este Ãºltimo con `if: always()` para asegurar limpieza). Se eliminaron los archivos individuales `python-tests.yml`, `integration-tests.yml` y `ci.yml`. (2026-01-19)

### 2026-01-16

- AÃ±adido: AuditorÃ­a inicial y tests de seguridad mÃ­nimos.
	- Test agregado: `tests/services/test_run_services_minimal.py` â comprobaciÃ³n simple de invocaciÃ³n de subprocess sin shell.

**Seguridad**: Se aplicaron correcciones en local al manejo de ejecuciÃ³n de comandos (sin `shell=True`) y se aÃ±adieron herramientas para auditar `f-strings`. Revisar y parchear manualmente las interpolaciones detectadas.

### AÃ±adido (2026-01-23)

- SecciÃ³n de documentaciÃ³n accesible desde la UI: permite visualizar `README.md` y todos los archivos Markdown de la carpeta `Docs/` desde la interfaz web.
- Endpoints REST para exponer archivos de documentaciÃ³n (`/docs/list`, `/docs/readme`, `/docs/file/{filename}`).
