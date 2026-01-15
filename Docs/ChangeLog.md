# Registro de cambios

Todos los cambios notables de este proyecto se documentarán en este archivo.

El formato se basa en "Keep a Changelog" y este proyecto sigue el Versionado Semántico.

## [Sin publicar]

### Añadido
- Endpoint `POST /network/scan_range`: escanea un CIDR o un rango de IPs y devuelve, por host, los puertos abiertos/cerrados/filtrados. (2026-01-14)
- UI: nueva operación "Análisis de redes (rango)" en el panel de operaciones de FastAPI; muestra una tarjeta por IP con los resultados de puertos y desplazamiento interno por tarjeta. (2026-01-14)
- Tests: `tests/controllers/test_network_api_scan_range.py` que cubre el fallback de CIDR y el rechazo de rangos grandes. (2026-01-14)
- Docs: `Docs/Network_Scan_Range.md` que describe la API, el uso de la UI y ejemplos. (2026-01-14)
 - UI: nueva categoría `OSINT` en el panel de `Operaciones FastAPI` que agrupa las subsecciones `Scrapy`, `SpaCy`, `Tiny` y `LLM` para facilitar el acceso a operaciones relacionadas con inteligencia de fuentes abiertas. (2026-01-15)

### Cambiado
- El servicio de escaneo de red (`app.services.network_analysis.network_analysis`) ahora incluye un campo explícito `state` para los resultados analizados por nmap (p. ej., `open`, `closed`, `filtered`) para permitir el renderizado correcto en la UI de puertos filtrados. (2026-01-14)
- UI (`src/app/ui/static/ui.js`, `styles.css`) muestra una insignia `FILTERED` (naranja) para `state === 'filtered'`; ordena hosts y puertos para priorizar resultados abiertos/filtrados; las tarjetas incluyen colapsado/expandido y altura limitada para la lista de puertos con desplazamiento interno. (2026-01-14)

### Corregido
- Mejoras de validación: `RangeScanRequest` normaliza cadenas vacías y acepta `start`/`end` cuando `cidr` está vacío; mejor manejo de payloads de formulario para evitar errores 422 desde la UI. (2026-01-14)

### Seguridad
- Las solicitudes de escaneo están limitadas a un máximo de 1024 hosts por petición para prevenir escaneos masivos accidentales. (2026-01-14)


## [0.0.0] - 2026-01-14
- Entrada inicial de notas de la versión (desarrollo interno)
