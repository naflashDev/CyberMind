# 📚 Fuentes de Datos y Recolección

# Definición

Obtención de fuentes y métodos utilizados para la recolección automatizada de información relacionada con **vulnerabilidades en tecnologías IT y OT**. La información recolectada se utiliza como base para procesos de análisis, documentación, inteligencia y respuesta ante amenazas.

---

## Métodos de Recolección

### 1. Feeds RSS/Atom (Google Alerts)

Se utilizan Google Alerts configurados con palabras clave específicas para detectar noticias, reportes y publicaciones relevantes. De estos alerts se extrae la web que contiene la información, en busca de nuevos feeds RSS o Atom, los cuales son consumidos automáticamente mediante agregadores o scripts personalizados.

- Los feeds de Google Alerts se almacenan en el archivo `google_alert_rss.txt`de forma manual.  
- Desde este archivo se extraen webs limpias que podrían contener feeds relevantes en ciberseguridad.  
- Las webs extraídas se almacenan junto con otras obtenidas mediante técnicas de Google Dorking en el archivo `urls_cybersecurity_ot_it.txt`.


- **Ejemplos de palabras clave:**
  - `ciberseguridad IT`
  - `ciberseguridad OT`
  - `ciberataque OT`
  - `ciberataque IT`
  - `industrial control system attack`
  - `SCADA attack`
  - `Otros` 

- **Herramientas recomendadas:**
  - Feedparser Para leer y analizar feeds RSS/Atom de Google Alerts
  - Urllib.parse Para extraer y limpiar URLs reales desde enlaces redirigidos de Google
  - Scripts en Python

---

### 2. Google Dorking

Se emplean técnicas de **Google Dorking** para realizar búsquedas avanzadas con el objetivo de encontrar documentos técnicos, publicaciones, investigaciones y noticias ocultas en resultados convencionales.

- **Ejemplos de dorks utilizados:**
  - `inurl:/scada filetype:pdf site:.gov`
  - `"PLC vulnerability" site:ics-cert.us-cert.gov`
  - `intitle:"index of" "OT network"`
  - `"vulnerabilidad ICS" site:.edu OR site:.org`

- **Objetivo:**
  - Recolectar información técnica relevante no indexada de forma directa.
  - Identificar fuentes confiables y actualizadas en materia de seguridad OT/IT.
  - Extraer noticias específicas y posibles feeds RSS de medios especializados.
  - Detectar enlaces a reportes técnicos, boletines RSS y archivos PDF públicos.

- **Frecuencia:**
  - Consultas automatizadas cada 24 horas.
  - Consultas programadas con rotación de agentes de usuario y retardos aleatorios.

#### Automatización y Procesamiento

Se han desarrollado scripts en **Python** para automatizar todo el flujo:

- **Módulo de Búsqueda:**
  - Utiliza `googlesearch` para ejecutar las consultas de dorking.
  - Extrae las URLs devueltas por Google.

- **Módulo de Extracción y Filtrado:**
  - Usa `httpx` y `BeautifulSoup` para obtener el contenido HTML de las páginas.
  - Analiza los textos de encabezados (`h1`–`h6`) y párrafos (`p`).
  - Aplica un filtro de relevancia basado en coincidencias con keywords como:
    `SCADA`, `OT`, `ciberseguridad`, `vulnerabilidad`, `malware`, etc.

- **Almacenamiento:**
  - Las noticias relevantes se guardan en `src/outputs/result.json` como estructuras enriquecidas con metadatos (`title`, `h1`, `p`, etc.).
  - Las URLs encontradas que podrían contener **feeds RSS o Atom** se almacenan en:
    ```bash
    src/data/urls_cybersecurity_ot_it.txt
    ```
    para su posterior análisis con **Scrapy** u otros agregadores como Tiny Tiny RSS.

---

#### Archivos Generados

| Archivo | Descripción |
|--------|-------------|
| `src/outputs/result.json` | JSON estructurado con artículos relevantes sobre seguridad OT/IT |
| `src/data/urls_cybersecurity_ot_it.txt` | Lista de URLs candidatas a contener feeds RSS |

---

#### Nota

La técnica de Google Dorking no solo permite encontrar documentos técnicos y vulnerabilidades publicadas, sino también detectar medios digitales que ofrecen **fuentes RSS** de alto valor para la inteligencia de amenazas en entornos industriales. Estas fuentes alimentan módulos adicionales de scraping o agregación automática.

    
---

## Temáticas de Interés

Los datos recolectados están centrados en:

- Vulnerabilidades recientes (CVE) en sistemas IT y dispositivos OT/ICS
- Exposición de activos industriales conectados a internet
- Campañas activas de malware dirigidas a infraestructuras críticas
- Informes técnicos y análisis forense de incidentes OT
- Boletines de seguridad de fabricantes de hardware o software industrial

---

## Uso de la Información

La información obtenida mediante estos métodos se emplea para:

- Enriquecer informes de inteligencia y análisis de amenazas
- Procesar el texto para detectar entidades nombradas
- Extraer etiquetas relevantes para indexar en OpenSearch como campos adicionales.

---