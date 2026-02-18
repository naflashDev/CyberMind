# 🧠 CyberMind – Plataforma Multifunción de Ciberseguridad y Auditoría

**CyberMind** es una plataforma modular, automatizada y de código abierto para la auditoría, análisis, monitorización y automatización de tareas de ciberseguridad en entornos **IT** y **OT**. Va mucho más allá de la simple recolección de datos: permite realizar auditorías técnicas, análisis de vulnerabilidades, orquestación de flujos de trabajo, generación de dashboards, integración de IA y procesamiento avanzado de información.

> 🎯 **Objetivo:** Proveer una solución integral y flexible para la gestión de inteligencia, auditoría y automatización en ciberseguridad, facilitando el acceso a datos estructurados y procesados, la correlación de eventos y la toma de decisiones informada. Promueve la transparencia, la colaboración abierta y el uso de metodologías de inteligencia y automatización.

---

## 👥 ¿A quién va dirigido?

Investigadores, periodistas de datos, analistas y desarrolladores interesados en contribuir con nuevos módulos, fuentes y casos de uso.

---


## 🧭 Objetivos principales

- Automatizar la recolección, análisis y correlación de información de ciberseguridad desde múltiples fuentes (noticias, feeds, APIs, escaneos de red, etc.).
- Facilitar auditorías técnicas y análisis de vulnerabilidades en infraestructuras IT/OT.
- Orquestar flujos de trabajo y tareas periódicas (scraping, procesamiento NLP, actualización de modelos, etc.).
- Procesar información no estructurada usando técnicas de NLP, machine learning y modelos LLM.
- Detectar patrones, narrativas, entidades clave y anomalías en grandes volúmenes de datos.
- Correlacionar eventos y datos de fuentes heterogéneas (noticias, estadísticas, vulnerabilidades, escaneos, logs).
- Visualizar resultados mediante dashboards, informes y paneles interactivos.
- Servir como base para entrenar y evaluar modelos de lenguaje adaptados a ciberseguridad.
- Permitir la integración de nuevos módulos, plugins y servicios para ampliar capacidades.

---


## ⚙️ Características destacadas

| Característica | Descripción |
|:---|:---|
| 🔁 Orquestación y automatización | Orquestación de tareas de recolección, análisis, escaneo, procesamiento NLP, actualización de modelos y generación de informes. Integración opcional con Airflow u otros programadores. |
| 🌐 Multifuente y multipropósito | Integración con RSS (TinyRSS), Google Alerts, Google Dorking, APIs públicas, escaneos de red, logs, bases de datos y más. |
| 🧠 Procesamiento semántico y ML | Extracción de keywords, NER, sentimiento, embeddings, categorización y análisis avanzado con NLP y machine learning. |
| 🗂️ Almacenamiento híbrido | OpenSearch para búsquedas semánticas, PostgreSQL para datos estructurados, soporte para outputs customizados. |
| 📊 Dashboards e informes | Visualización configurable con OpenSearch Dashboards. |
| 🤖 Integración de IA y LLM | Módulo de IA especializado en ciberseguridad, consultas técnicas, resumen de CVEs, análisis de noticias y soporte a auditoría. |
| 🛡️ Auditoría y análisis de red | Funciones de escaneo de red, análisis de puertos, correlación de vulnerabilidades y soporte a auditoría técnica. |
| 🧩 Arquitectura modular y extensible | Permite incorporar nuevos dominios, módulos, plugins y servicios de forma independiente. |

---


## 🧪 Casos de uso iniciales

- **Auditoría y análisis de infraestructuras IT/OT:** Escaneo de red, análisis de puertos, correlación de vulnerabilidades, generación de informes técnicos.
- **Automatización de flujos de inteligencia:** Orquestación de scraping, procesamiento NLP, actualización de modelos y generación de dashboards.
- **Análisis y monitorización de amenazas:** Detección y correlación de CVEs, CWE, CAPEC, noticias y eventos de ciberseguridad.
- **Entrenamiento y evaluación de modelos LLM para ciberseguridad:** Modelos adaptados a la detección y análisis de amenazas OT/IT, generación de datasets y validación de resultados.

---

## 🚀 Filosofía open source

- Fomentar la colaboración entre comunidades técnicas y académicas.
- Proveer una infraestructura reutilizable para proyectos de investigación aplicada.
- Crear un ecosistema de plugins y módulos para ampliar capacidades.
- Servir como punto de partida para iniciativas públicas o ciudadanas de análisis e inteligencia de datos.

---

## 🌍 Acceso y despliegue

Puedes clonar e instalar localmente o adaptar la plataforma para nuevos fines.

> ℹ️ **Consulta el resto de la documentación para guías de instalación, arquitectura, API y casos de uso avanzados.**

---


## Definiciones y enfoque multifunción

**CyberMind** integra y automatiza técnicas de recolección, análisis, auditoría y procesamiento de información para ciberseguridad, combinando metodologías OSINT, escaneo de red, análisis de vulnerabilidades, procesamiento NLP/ML y generación de dashboards. No es solo una herramienta de recolección, sino una plataforma multifunción para la gestión y automatización de inteligencia y auditoría técnica.

### Ejemplos de capacidades:
- Recolección y análisis de fuentes abiertas (OSINT): feeds, noticias, APIs, Google Dorking, etc.
- Auditoría y escaneo de red: análisis de puertos, correlación de vulnerabilidades, generación de informes técnicos.
- Procesamiento avanzado de texto: NLP, extracción de entidades, categorización, sentimiento, embeddings, clustering.
- Automatización de flujos: scraping, procesamiento periódico, actualización de modelos, generación de dashboards.
- Generación de datasets y entrenamiento de modelos LLM para ciberseguridad.
- Visualización y reporting: dashboards, informes, paneles interactivos.

> 💡 *CyberMind apuesta por una tecnología transparente, abierta, colaborativa y orientada a la automatización y la auditoría avanzada en ciberseguridad.*

---

## 🖥️ Mejora de usabilidad en System Status (UI)

Se ha mejorado la sección "System Status" de la interfaz de usuario añadiendo los siguientes cambios:

- **Nombres amigables para los workers:** Ahora los nombres de los workers se muestran de forma legible y coherente con los botones de la UI.
- **Icono de información:** Se ha añadido un icono ℹ️ junto a cada worker. Al hacer hover, se muestra una breve descripción de la función de cada worker.

**Beneficios:**
- Mayor claridad para el usuario sobre el propósito de cada worker.
- Experiencia de usuario más intuitiva y profesional.

**Ejemplo:**

| Worker           | Nombre mostrado      | Tooltip (descripción)                                      |
|------------------|---------------------|------------------------------------------------------------|
| google_alerts    | Google Alerts       | Recolecta alertas de Google configuradas y las procesa periódicamente. |
| rss_extractor    | Extractor RSS       | Extrae y normaliza feeds RSS de ciberseguridad desde fuentes configuradas. |
| scraping_feeds   | Scraping Feeds      | Rastrea y actualiza feeds de noticias de ciberseguridad.    |
| scraping_news    | Scraping News       | Extrae artículos y noticias de fuentes externas para su análisis. |
| spacy_nlp        | NLP (spaCy)         | Procesa y etiqueta entidades en textos usando spaCy cada 24h. |
| llm_updater      | LLM Updater         | Actualiza el modelo LLM y el dataset de CVEs cada 7 días.   |
| dynamic_spider   | Spider Dinámico     | Ejecuta spiders Scrapy configurados dinámicamente desde la base de datos. |

