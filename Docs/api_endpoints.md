++"""markdown
# API Endpoints

Este documento resume los endpoints públicos expuestos por la API de CyberMind. Puedes probarlos desde la UI o usando `curl` / `httpie`. La documentación interactiva (Swagger) está disponible en `http://127.0.0.1:8000/docs` cuando la API está en ejecución.

## Raíz y UI
- `GET /` — Redirige o devuelve información básica (no incluida en el esquema Swagger).
- `GET /ui` — Página web de la UI (servida desde `src/app/ui/static`).

## News Spider (`/newsSpider`)
Prefijo: `/newsSpider`

- `POST /newsSpider/save-feed-google-alerts` — Añade y valida un feed RSS (body: `{ "feed_url": "https://..." }`).
  - Respuesta: `SaveLinkResponse` con título y link guardado.
- `GET /newsSpider/scrape-news` — Lanza el proceso de scraping de noticias (background task).
- `GET /newsSpider/start-google-alerts` — Inicia el programador periódico que procesa los feeds listados en `data/google_alert_rss.txt`.
- `GET /newsSpider/scrapy/google-dk/feeds` — Inicia scraping de feeds usando Google Dorking (tarea programada cada 24h).
- `GET /newsSpider/scrapy/google-dk/news` — Inicia scraping de noticias usando Google Dorking (tarea programada cada 24h).

Uso típico (curl):

```bash
curl -X POST http://127.0.0.1:8000/newsSpider/save-feed-google-alerts -H "Content-Type: application/json" -d '{"feed_url":"https://example.com/rss"}'
```

## TinyRSS/Postgres (`/postgre-ttrss`)
Prefijo: `/postgre-ttrss`

- `GET /postgre-ttrss/search-and-insert-rss` — Lanza la extracción periódica de URLs listadas en `data/urls_cybersecurity_ot_it.txt` y persiste los feeds en Postgres.
- `GET /postgre-ttrss/feeds?limit=10` — Devuelve feeds guardados en la BD, con parámetro `limit` (por defecto 10).

Ejemplo:

```bash
curl http://127.0.0.1:8000/postgre-ttrss/feeds?limit=20
```

## LLM (`/llm`)
Prefijo: `/llm`

- `POST /llm/query` — Envía un `prompt` y devuelve la respuesta del LLM.
  - Body: `{ "prompt": "Explica CVE-2024-XXXX" }`
  - Respuesta: `{ "response": "..." }`
- `GET /llm/updater` — Inicia el proceso de actualización/finetune periódico del LLM (background loop semanal).
- `GET /llm/stop-updater` — Detiene el proceso iniciado por `/llm/updater`.

Ejemplo de consulta al LLM:

```bash
curl -X POST http://127.0.0.1:8000/llm/query -H "Content-Type: application/json" -d '{"prompt":"Resume CVE-2024-4320"}'
```

### Integración con la UI

La UI proporciona controles para iniciar/detener el `llm_updater` y para enviar consultas al LLM desde el panel interactivo. En la UI, las solicitudes se envían al endpoint `/llm/query` y al endpoint `/llm/updater` para controlar el proceso de actualización.

### Comportamiento y alcance del LLM

- El LLM integrado está especializado en ciberseguridad: responde a consultas relacionadas con CVE, análisis técnico, forense digital, y noticias recogidas por los scrapers del sistema.
- No es una búsqueda generalista: su conocimiento está orientado a la información procesada por la plataforma (CVE, artefactos técnicos, resúmenes de noticias).
- Recomendación de uso: formular preguntas concretas sobre vulnerabilidades, descripciones técnicas y resúmenes de noticias; evita pedir información fuera del dominio técnico.

## SpaCy (`/start-spacy`)
- `GET /start-spacy` — Inicia un proceso background que lee `outputs/result.json`, extrae entidades y escribe `outputs/labels_result.json`. Programado para ejecutarse cada 24 horas si se lanza desde la API.

## Estado y control (`/status`, `/workers/*`)
- `GET /status` — Devuelve un objeto JSON con el estado del sistema, listando workers y flags de inicialización.
- `POST /workers/{worker_name}` — Controla (activar/desactivar) workers desde la UI (se espera body `{ "enabled": true|false }`).

Ejemplo:

```bash
curl http://127.0.0.1:8000/status
curl -X POST http://127.0.0.1:8000/workers/rss_extractor -H "Content-Type: application/json" -d '{"enabled":true}'
```

## Network (`/network`)
Prefijo: `/network`

- `POST /network/scan` — Escanea puertos TCP del host indicado y devuelve una lista de puertos con indicador `open` y una etiqueta heurística de servicio.
  - Body: `{ "host": "1.2.3.4", "ports": [22,80], "timeout": 0.5 }` (el campo `ports` es opcional; si se omite se usan puertos comunes).
  - Respuesta: `{ "host": "1.2.3.4", "results": [{"port":22,"open":true,"service":"ssh"}, ...] }`

- `GET /network/ports` — Devuelve una lista de puertos comunes sugeridos para escaneo.

### Escaneo por rango / CIDR

- `POST /network/scan_range` — Escanea un rango de IPs (por CIDR o por start/end) y devuelve, por cada host, la lista de puertos analizados junto con su `state`.
  - Body (JSON):
    - `cidr` (string, opcional): bloque CIDR (ej. `192.168.1.0/28`). Si se proporciona, se escanean las IPs del bloque. Si está vacío (`""`) se trata como omitido.
    - `start` (string, opcional): IP inicial del rango (ej. `192.168.1.3`). Se usa cuando `cidr` no está presente.
    - `end` (string, opcional): IP final del rango. Si no se proporciona, se escanea solo `start`.
    - `ports` (array de ints o string CSV, opcional): lista de puertos a escanear. La UI puede enviar CSV (`"22,80,443"`) o un arreglo JSON.
    - `timeout` (number, opcional): timeout por host para `nmap` (segundos). El fallback TCP usa un timeout menor (p. ej. 0.5s).
    - `use_nmap` (bool, opcional): si `true`, intenta ejecutar `nmap -sV`; si `nmap` no está disponible se usa un fallback TCP.
    - `concurrency` (int, opcional): máximo de tareas concurrentes (por seguridad el servidor aplica un valor por defecto y límites).

  - Restricciones y validaciones:
    - Límite por petición: máximo 1024 hosts. Si el bloque/rango supera ese límite, la API responde `400` con detalle.
    - Se valida que `end >= start` cuando ambos son IPs.

  - Respuesta (ejemplo simplificado):

```json
{
  "scanned": 2,
  "hosts": [
    {
      "host": "192.168.1.1",
      "results": [
        {"port":22,"open":true,"state":"open","service":"ssh"},
        {"port":80,"open":false,"state":"filtered","service":"http"}
      ],
      "duration_seconds": 0.45
    }
  ],
  "duration_seconds": 1.23
}
```

  - Notas importantes:
    - Cada elemento en `results` incluye `state` además de `open`. Valores observados: `open`, `closed`, `filtered`, `unknown`.
    - La UI interpreta `state === 'filtered'` y muestra un badge naranja; `open` mostrará badge verde; cualquier otro estado se considera `CLOSED` (rojo) en la vista.

  - Uso en la UI: Panel "Controllers" → sección "Network" → Operación "Análisis de redes (rango)". Parámetros: completar `cidr` O `start` (+ opcional `end`), ajustar `ports`, `use_nmap` y `concurrency`.

  - Ejemplo cURL (CIDR, fallback TCP):

```bash
curl -X POST http://127.0.0.1:8000/network/scan_range \
  -H "Content-Type: application/json" \
  -d '{"cidr":"127.0.0.0/30","use_nmap":false,"ports":[22,80,443]}'
```

  - Ejemplo cURL (start–end, intentar nmap):

```bash
curl -X POST http://127.0.0.1:8000/network/scan_range \
  -H "Content-Type: application/json" \
  -d '{"start":"192.168.1.2","end":"192.168.1.5","use_nmap":true,"concurrency":10}'
```

  - Nota legal: realizar escaneos de red contra hosts ajenos puede ser intrusivo y requiere autorización. Usa estas herramientas solo contra sistemas que controlas o tienes permiso explícito para analizar.

Ejemplo (scan):

```bash
curl -X POST http://127.0.0.1:8000/network/scan -H "Content-Type: application/json" -d '{"host":"8.8.8.8","ports":[53,80]}'
```

Nota legal: Realizar escaneos de red contra hosts ajenos puede ser intrusivo y requiere autorización. Usa estas herramientas solo contra sistemas que controlas o tienes permiso explícito para analizar.

## Notas
- La UI (`/ui`) ofrece controles que llaman a estos endpoints y muestra el estado en tiempo real.
- Para ver tipos y modelos, consulta la documentación interactiva en `http://127.0.0.1:8000/docs`.

Si quieres que genere ejemplos más detallados (cURL con autenticación, respuestas esperadas, o fragmentos de Python), dime cuáles endpoints priorizar.
"""