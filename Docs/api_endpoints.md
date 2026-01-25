# 🚀 **Endpoints de la API CyberMind**
<div align="center">
  <img src="https://img.shields.io/badge/API-RESTful-009688?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Seguridad-By%20Design-4ECDC4?style=for-the-badge" />
  <img src="https://img.shields.io/badge/IA-Integrada-7B68EE?style=for-the-badge" />
</div>
<div align="center">
  <strong>Plataforma modular para automatización, análisis y auditoría de ciberseguridad IT/OT</strong>
</div>

---

<details>
<summary><strong>ℹ️ Descripción general</strong></summary>

**CyberMind** es una plataforma multifunción que integra:

- 🕸️ Scraping y feeds
- 🤖 Procesamiento semántico y LLM
- 🛡️ Análisis de vulnerabilidades
- 🌐 Escaneo de red
- 🗂️ Orquestación de tareas
- 📊 Dashboards y reporting

Permite desde la recolección y correlación de datos hasta la ejecución de auditorías técnicas, automatización de flujos y generación de informes avanzados.

<div align="center">
  <b>Todos los endpoints pueden probarse desde la UI o con herramientas como <code>curl</code> o <code>httpie</code>.</b>
</div>

> 📑 <b>Documentación interactiva (Swagger):</b> <br>
> Accede a <a href="http://127.0.0.1:8000/docs">http://127.0.0.1:8000/docs</a> para explorar y probar los endpoints de forma visual.

</details>

---

## 🏠 **Raíz y UI**

<table>
  <thead>
    <tr>
      <th>Método</th>
      <th>Ruta</th>
      <th>Descripción</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>GET</b></td>
      <td><code>/</code></td>
      <td>Redirige o devuelve información básica (no incluida en Swagger)</td>
    </tr>
    <tr>
      <td><b>GET</b></td>
      <td><code>/ui</code></td>
      <td>Página web de la UI (servida desde <code>src/app/ui/static</code>)</td>
    </tr>
  </tbody>
</table>

---



## 🕸️ **News Spider** <code>(/newsSpider)</code>

<details>
<summary><b>📥 Ver endpoints de scraping y feeds</b></summary>

<table>
  <thead>
    <tr>
      <th>Método</th>
      <th>Ruta</th>
      <th>Descripción</th>
      <th>Body/Parámetros</th>
      <th>Respuesta</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>POST</b></td>
      <td><code>/newsSpider/save-feed-google-alerts</code></td>
      <td>Añade y valida un feed RSS</td>
      <td><code>{ "feed_url": "https://..." }</code></td>
      <td><code>SaveLinkResponse</code> (título y link)</td>
    </tr>
    <tr>
      <td><b>GET</b></td>
      <td><code>/newsSpider/scrape-news</code></td>
      <td>Lanza scraping de noticias (background)</td>
      <td>—</td>
      <td>—</td>
    </tr>
    <tr>
      <td><b>GET</b></td>
      <td><code>/newsSpider/start-google-alerts</code></td>
      <td>Inicia el programador periódico para feeds de <code>data/google_alert_rss.txt</code></td>
      <td>—</td>
      <td>—</td>
    </tr>
    <tr>
      <td><b>GET</b></td>
      <td><code>/newsSpider/scrapy/google-dk/feeds</code></td>
      <td>Scraping de feeds con Google Dorking (cada 24h)</td>
      <td>—</td>
      <td>—</td>
    </tr>
    <tr>
      <td><b>GET</b></td>
      <td><code>/newsSpider/scrapy/google-dk/news</code></td>
      <td>Scraping de noticias con Google Dorking (cada 24h)</td>
      <td>—</td>
      <td>—</td>
    </tr>
  </tbody>
</table>

<blockquote>
<b>Ejemplo de uso (curl):</b>

<pre><code>curl -X POST http://127.0.0.1:8000/newsSpider/save-feed-google-alerts -H "Content-Type: application/json" -d '{"feed_url":"https://example.com/rss"}'
</code></pre>
</blockquote>

</details>

---



## 📰 **TinyRSS/Postgres** <code>(/postgre-ttrss)</code>

<details>
<summary><b>📥 Ver endpoints de feeds y almacenamiento</b></summary>

<table>
  <thead>
    <tr>
      <th>Método</th>
      <th>Ruta</th>
      <th>Descripción</th>
      <th>Parámetros</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>GET</b></td>
      <td><code>/postgre-ttrss/search-and-insert-rss</code></td>
      <td>Extrae periódicamente URLs de <code>data/urls_cybersecurity_ot_it.txt</code> y persiste feeds en Postgres</td>
      <td>—</td>
    </tr>
    <tr>
      <td><b>GET</b></td>
      <td><code>/postgre-ttrss/feeds?limit=10</code></td>
      <td>Devuelve feeds guardados en la BD (por defecto 10)</td>
      <td><code>limit</code> (opcional)</td>
    </tr>
  </tbody>
</table>

<blockquote>
<b>Ejemplo:</b>

<pre><code>curl http://127.0.0.1:8000/postgre-ttrss/feeds?limit=20
</code></pre>
</blockquote>

</details>

---



## 🤖 **LLM** <code>(/llm)</code>

<details>
<summary><b>🧠 Endpoints de IA y consultas técnicas</b></summary>

### Descripción general
El módulo LLM de CyberMind utiliza un modelo **LLama3** restringido, configurado mediante un archivo **Model file** que limita sus respuestas y comportamiento. Su base de conocimiento está limitada hasta el año **2023** y no incluye información posterior. El modelo responde únicamente sobre temas de ciberseguridad y CVE según las restricciones del Model file. El finetuning con datos propios está planificado como mejora futura, pero el archivo JSON para el finetuning **sí se genera** automáticamente (`outputs/finetune_data.jsonl`), aunque no se utiliza aún para entrenar el modelo.

> ⚠️ **Importante:** El modelo actual **NO ha sido finetuneado** con los datos extraídos por el sistema. La función de entrenamiento personalizado (finetuning) se implementará en el futuro, ya que el proceso es altamente demandante en recursos y tiempo.

### Endpoints disponibles

<table>
  <thead>
    <tr>
      <th>Método</th>
      <th>Ruta</th>
      <th>Descripción</th>
      <th>Body/Parámetros</th>
      <th>Respuesta</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>POST</b></td>
      <td><code>/llm/query</code></td>
      <td>Envía un <code>prompt</code> y devuelve la respuesta del LLM</td>
      <td><code>{ "prompt": "Explica CVE-2024-XXXX" }</code></td>
      <td><code>{ "response": "..." }</code></td>
    </tr>
    <tr>
      <td><b>GET</b></td>
      <td><code>/llm/updater</code></td>
      <td>Inicia el proceso de actualización/finetune periódico del LLM</td>
      <td>—</td>
      <td>—</td>
    </tr>
    <tr>
      <td><b>GET</b></td>
      <td><code>/llm/stop-updater</code></td>
      <td>Detiene el proceso iniciado por <code>/llm/updater</code></td>
      <td>—</td>
      <td>—</td>
    </tr>
  </tbody>
</table>

<blockquote>
<b>Ejemplo de consulta al LLM:</b>

<pre><code>curl -X POST http://127.0.0.1:8000/llm/query -H "Content-Type: application/json" -d '{"prompt":"Resume CVE-2024-4320"}'
</code></pre>
</blockquote>

</details>

---



## 🖥️ **Integración con la UI y flujos multifunción**

<details>
<summary><b>🖱️ ¿Qué permite la UI de CyberMind?</b></summary>

- Iniciar/detener el <code>llm_updater</code> y otros workers de automatización
- Enviar consultas al LLM especializado en ciberseguridad
- Acceder a paneles de auditoría, análisis de red, scraping, procesamiento NLP, reporting y dashboards
- Orquestar flujos de trabajo: scraping, análisis, escaneo, generación de informes y dashboards
- Visualizar resultados en tiempo real y acceder a informes técnicos generados automáticamente

<br/>

<b>Las categorías de la UI agrupan accesos rápidos a:</b>

| Categoría | Funcionalidad |
|---|---|
| <b>Scrapy</b> | Scraping de noticias, feeds, Google Alerts, Google Dorking |
| <b>SpaCy</b> | Procesamiento NLP, extracción de entidades, análisis semántico |
| <b>TinyRSS/Postgres</b> | Gestión y consulta de feeds estructurados |
| <b>LLM</b> | Consultas técnicas, resumen de CVEs, análisis de noticias y soporte a auditoría |
| <b>Network</b> | Escaneo de red, análisis de puertos, correlación de vulnerabilidades |
| <b>Dashboards/Reporting</b> | Visualización de resultados, generación de informes y paneles interactivos |

Cada subsección expande su listado de operaciones (botones) que ejecutan llamadas HTTP a los endpoints descritos en este documento. Por ejemplo, al seleccionar <code>Network</code> se muestran los botones para escaneo de red, análisis de puertos o generación de informes técnicos.

<br/>

<b>Comportamiento y alcance del LLM:</b>

- El LLM integrado está especializado en ciberseguridad: responde a consultas sobre CVE, análisis técnico, forense digital, noticias, correlación de vulnerabilidades y soporte a auditoría.
- No es una búsqueda generalista: su conocimiento está orientado a la información procesada y auditada por la plataforma.
- Recomendación de uso: formular preguntas concretas sobre vulnerabilidades, auditoría, descripciones técnicas, resúmenes de noticias y análisis de red.

</details>

---
## 🌐 **Network (`/network`)**

<details>
<summary><b>🔎 Endpoints de escaneo y análisis de red</b></summary>

<ul>
<li><b>POST /network/scan</b> — Escanea puertos TCP del host indicado y devuelve una lista de puertos con indicador <code>open</code> y una etiqueta heurística de servicio.<br>
<b>Body:</b> <code>{ "host": "1.2.3.4", "ports": [22,80], "timeout": 0.5 }</code> (el campo <code>ports</code> es opcional; si se omite se usan puertos comunes).<br>
<b>Respuesta:</b> <code>{ "host": "1.2.3.4", "results": [{"port":22,"open":true,"service":"ssh"}, ...] }</code>
</li>
<li><b>GET /network/ports</b> — Devuelve una lista de puertos comunes sugeridos para escaneo.</li>
</ul>

<details>
<summary><b>🟦 Escaneo por rango / CIDR</b></summary>

- <b>POST /network/scan_range</b> — Escanea un rango de IPs (por CIDR o por start/end) y devuelve, por cada host, la lista de puertos analizados junto con su <code>state</code>.
  - <b>Body (JSON):</b>
    - <code>cidr</code> (string, opcional): bloque CIDR (ej. <code>192.168.1.0/28</code>). Si se proporciona, se escanean las IPs del bloque. Si está vacío (<code>""</code>) se trata como omitido.
    - <code>start</code> (string, opcional): IP inicial del rango (ej. <code>192.168.1.3</code>). Se usa cuando <code>cidr</code> no está presente.
    - <code>end</code> (string, opcional): IP final del rango. Si no se proporciona, se escanea solo <code>start</code>.
    - <code>ports</code> (array de ints o string CSV, opcional): lista de puertos a escanear. La UI puede enviar CSV (<code>"22,80,443"</code>) o un arreglo JSON.
    - <code>timeout</code> (number, opcional): timeout por host para <code>nmap</code> (segundos). El fallback TCP usa un timeout menor (p. ej. 0.5s).
    - <code>use_nmap</code> (bool, opcional): si <code>true</code>, intenta ejecutar <code>nmap -sV</code>; si <code>nmap</code> no está disponible se usa un fallback TCP.
    - <code>concurrency</code> (int, opcional): máximo de tareas concurrentes (por seguridad el servidor aplica un valor por defecto y límites).

  - <b>Restricciones y validaciones:</b>
    - Límite por petición: máximo 1024 hosts. Si el bloque/rango supera ese límite, la API responde <code>400</code> con detalle.
    - Se valida que <code>end >= start</code> cuando ambos son IPs.

  - <b>Respuesta (ejemplo simplificado):</b>

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

  - <b>Notas importantes:</b>
    - Cada elemento en <code>results</code> incluye <code>state</code> además de <code>open</code>. Valores observados: <code>open</code>, <code>closed</code>, <code>filtered</code>, <code>unknown</code>.
    - La UI interpreta <code>state === 'filtered'</code> y muestra un badge naranja; <code>open</code> mostrará badge verde; cualquier otro estado se considera <b>CLOSED</b> (rojo) en la vista.

  - <b>Uso en la UI:</b> Panel "Controllers" → sección "Network" → Operación "Análisis de redes (rango)". Parámetros: completar <code>cidr</code> O <code>start</code> (+ opcional <code>end</code>), ajustar <code>ports</code>, <code>use_nmap</code> y <code>concurrency</code>.

  - <b>Ejemplo cURL (CIDR, fallback TCP):</b>

```bash
curl -X POST http://127.0.0.1:8000/network/scan_range \
  -H "Content-Type: application/json" \
  -d '{"cidr":"127.0.0.0/30","use_nmap":false,"ports":[22,80,443]}'
```

  - <b>Ejemplo cURL (start–end, intentar nmap):</b>

```bash
curl -X POST http://127.0.0.1:8000/network/scan_range \
  -H "Content-Type: application/json" \
  -d '{"start":"192.168.1.2","end":"192.168.1.5","use_nmap":true,"concurrency":10}'
```

  - <b>Nota legal:</b> realizar escaneos de red contra hosts ajenos puede ser intrusivo y requiere autorización. Usa estas herramientas solo contra sistemas que controlas o tienes permiso explícito para analizar.

</details>

</details>

---

## 🧩 **Endpoints adicionales y utilidades**

<details>
<summary><b>🟣 SpaCy (`/start-spacy`)</b></summary>

- <b>GET /start-spacy</b> — Inicia un proceso background que lee <code>outputs/result.json</code>, extrae entidades y escribe <code>outputs/labels_result.json</code>. Programado para ejecutarse cada 24 horas si se lanza desde la API.

</details>

<details>
<summary><b>🟢 Estado y control (`/status`, `/workers/*`)</b></summary>

- <b>GET /status</b> — Devuelve un objeto JSON con el estado del sistema, listando workers y flags de inicialización.
- <b>POST /workers/{worker_name}</b> — Controla (activar/desactivar) workers desde la UI (se espera body <code>{ "enabled": true|false }</code>).

<b>Ejemplo:</b>

```bash
curl http://127.0.0.1:8000/status
curl -X POST http://127.0.0.1:8000/workers/rss_extractor -H "Content-Type: application/json" -d '{"enabled":true}'
```

</details>
<details>
<summary><strong>⚙️ Endpoints de configuración y parámetros</strong></summary>

<div align="center">
  <img src="https://img.shields.io/badge/CONFIG-API%20Config-009688?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Ollama-Integraci%C3%B3n-7B68EE?style=for-the-badge" />
</div>

### Notas técnicas
- Los endpoints y la infraestructura soportan parámetros en formato dict extraídos de los archivos `.ini` (`clave=valor`).

---

### 📝 Endpoint: Configuración de archivos .ini

<table>
  <thead>
    <tr>
      <th>Método</th>
      <th>Ruta</th>
      <th>Descripción</th>
      <th>Body/Parámetros</th>
      <th>Respuesta</th>
      <th>Autenticación</th>
      <th>Códigos de estado</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>GET</b></td>
      <td><code>/config</code></td>
      <td>Devuelve los parámetros de los archivos .ini principales del sistema (<code>cfg_services.ini</code>, <code>cfg.ini</code>) en formato clave=valor.</td>
      <td>—</td>
      <td><code>{ files: [ { key, value, type } ] }</code></td>
      <td>No requiere</td>
      <td>200 OK, 500 Error interno</td>
    </tr>
    <tr>
      <td><b>POST</b></td>
      <td><code>/config</code></td>
      <td>Actualiza los parámetros de configuración.</td>
      <td><code>{ params: [ { key, value } ] }</code></td>
      <td>—</td>
      <td>No requiere</td>
      <td>200 OK, 404 Archivo no encontrado, 500 Error interno</td>
    </tr>
  </tbody>
</table>

---

### 💡 Formato de configuración soportado
- Las líneas principales de los archivos `.ini` deben estar en formato <code>clave=valor;clave=valor;...</code> para compatibilidad total con la edición vía API/UI.

---

### 🖥️ Notas de integración UI

#### Cambios visuales y de usabilidad (2026-01-24)
- El panel de configuración utiliza esquinas cuadradas para una integración visual sin huecos.
- Los textos de los parámetros de configuración se muestran con nombres amigables para el usuario.
- Todos los botones principales de la UI (guardar, descartar, operaciones) incluyen iconos representativos según su función.
- Diseño revisado para evitar huecos y mejorar la experiencia de usuario.

El endpoint <code>/config</code> es consultado por la UI para:
  - Mostrar/ocultar el apartado CyberSentinel IA según el parámetro <code>use_ollama</code>.
  - Mostrar correctamente el panel de configuración al pulsar el botón correspondiente, eliminando cualquier restricción de visibilidad por CSS o atributos <code>style</code>.

---

## 🟪 Parámetro de configuración: uso de Ollama

En el archivo <code>src/cfg_services.ini</code> se ha añadido el parámetro <code>use_ollama</code> para controlar la instalación y uso de Ollama.

**Funcionamiento actualizado (2026-01-24):**

**Ejemplo de línea de configuración:**
<pre><code>distro_name=Ubuntu;dockers_name=install-updater-1,install-web-nginx-1,install-app-1,install-db-1,opensearch-dashboards,opensearch;use_ollama=true
</code></pre>


Este parámetro puede modificarse manualmente para activar/desactivar el uso de Ollama según las necesidades del usuario y los recursos disponibles.

</details>

---


