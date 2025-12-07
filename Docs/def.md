# Definición del proyecto

# Introducción al Sistema Cebolla

La plataforma Cebolla es un sistema modular de código abierto diseñado para facilitar la obtención, estructuración, análisis y explotación de datos provenientes de fuentes públicas o privadas, tanto en tiempo real como mediante recolección histórica.

Su arquitectura se organiza en cinco grandes etapas:

1. **Recolección**
   - Captura de noticias y documentos desde:
     - Canales RSS mediante TinyRSS.
     - Alertas automáticas de Google Alerts.
     - Búsquedas avanzadas (OSINT) usando técnicas como Google Dorking.
     - Fuentes externas proporcionadas por el usuario (CSV, Excel, APIs).

2. **Extracción de Datos**
   - Transformación de información cruda en datos estructurados usando herramientas como:
     - Scrapy (HTML y web crawling).
     - Apache Tika / PyPDF2 (documentos y PDFs).
     - Whisper o Speech-to-Text (audio de vídeos).
     - Parsers específicos para emails y boletines.

3. **Procesamiento de Datos**
   - Aplicación de técnicas de NLP y Machine Learning:
     - spaCy, Hugging Face Transformers, LangChain.
     - Extracción de entidades, clasificación temática, análisis de sentimiento.
     - Asignación de keywords y relevancia para priorización.
     - Preparación para alimentar herramientas de inteligencia (MISP, AIL).

4. **Almacenamiento y Explotación**
   - Almacenamiento especializado según tipo de dato:
     - PostgreSQL: datos estructurados (estadísticas, configuraciones).
     - OpenSearch: texto y metadatos con búsqueda avanzada.

5. **Consumo y Visualización**
   - Los datos procesados podrán ser utilizados para:
     - Informes de inteligencia automatizados o personalizados.
     - Dashboards interactivos con Grafana, Chartbrew, D3.js.
     - Entrenamiento y evaluación de modelos LLM personalizados.

Todo el flujo es gestionado y automatizado mediante **Apache Airflow**, que permite orquestar procesos complejos y definir flujos de tareas en función del dominio, periodicidad, tipo de fuente y objetivos analíticos.