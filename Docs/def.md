
# 📝 Definición del Proyecto: Sistema Cebolla

El **Sistema Cebolla** es una plataforma modular de código abierto para la obtención, estructuración, análisis y explotación de datos de fuentes públicas o privadas, tanto en tiempo real como mediante recolección histórica.

---

## 🏗️ Arquitectura en 5 etapas

1. **Recolección**
   - Captura de noticias y documentos desde:
     - Canales RSS (TinyRSS)
     - Google Alerts automáticos
     - Búsquedas OSINT (Google Dorking)
     - Fuentes externas (CSV, Excel, APIs)

2. **Extracción de Datos**
   - Transformación de información cruda en datos estructurados usando:
     - Scrapy (web crawling)
     - Apache Tika / PyPDF2 (PDFs)
     - Whisper/Speech-to-Text (audio)
     - Parsers para emails y boletines

3. **Procesamiento de Datos**
   - Técnicas de NLP y Machine Learning:
     - spaCy, Hugging Face Transformers, LangChain
     - Extracción de entidades, clasificación temática, análisis de sentimiento
     - Asignación de keywords y relevancia
     - Preparación para herramientas de inteligencia (MISP, AIL)

4. **Almacenamiento y Explotación**
   - Almacenamiento especializado:
     - PostgreSQL: datos estructurados
     - OpenSearch: texto y metadatos con búsqueda avanzada

5. **Consumo y Visualización**
   - Uso de los datos procesados para:
     - Informes de inteligencia automatizados/personalizados
     - Dashboards interactivos (Grafana, Chartbrew, D3.js)
     - Entrenamiento y evaluación de modelos LLM personalizados

---

> ⚙️ **Automatización:** Todo el flujo es gestionado mediante **Apache Airflow**, que orquesta procesos complejos y define flujos de tareas según dominio, periodicidad, tipo de fuente y objetivos analíticos.