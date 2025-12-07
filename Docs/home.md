
# Proyecto Onion – Plataforma Abierta de Análisis de Información

**Onion** es una plataforma modular, automatizada y de código abierto para la recolección, análisis y visualización de información relevante sobre Las vulnerabilidades IT y OT (Tecnologías de la Información y Tecnologías de Operación). Su objetivo es facilitar el acceso a datos estructurados y procesados a partir de fuentes públicas, con enfoque en la transparencia, la colaboración abierta y el uso de metodologías de inteligencia.

El proyecto está orientado tanto a investigadores, periodistas de datos y analistas, como a desarrolladores interesados en contribuir con nuevas funcionalidades y dominios de análisis.

---

##  Definiciones



## 🧭 Objetivo del proyecto

Crear una herramienta abierta, extensible y replicable que permita:

- Recolectar noticias y documentos desde múltiples fuentes web.
- Procesar información no estructurada usando técnicas de NLP y machine learning.
- Detectar patrones, narrativas y entidades clave dentro de los textos.
- Correlacionar datos de fuentes heterogéneas (noticias, estadísticas, vulnerabilidades).
- Visualizar resultados mediante dashboards e interfaces interactivas.
- Servir como base para entrenar modelos de lenguaje adaptados a casos concretos.

---

## 🧩 Características principales

- 🔁 **Orquestación con Apache Airflow**: para automatizar flujos de recolección y análisis.
- 🌐 **Multifuente**: integraciones con RSS (TinyRSS), Google Alerts, Google Dorking, bases de datos públicas, APIs de seguridad, etc.
- 🧠 **Procesamiento semántico**: extracción de keywords, NER, sentimiento, embeddings vectoriales.
- 🗂️ **Almacenamiento híbrido**: OpenSearch para búsquedas semánticas.
- 📊 **Visualización abierta**: dashboards configurables con herramientas como Grafana o Chartbrew.
- 🧱 **Arquitectura modular**: diseñada para incorporar nuevos dominios de análisis de forma independiente.

---

## 🧪 Casos de uso iniciales

union está preparado para adaptarse a distintos dominios temáticos. Algunos de los primeros módulos en desarrollo incluyen:

- **Análisis de vulnerabilidades tecnológicas**: detección y correlación de CVEs, CWE, CAPEC, y noticias sobre ciberseguridad.
- **Entrenamiento de un LLM sobre ciberseguridad industrial**: detección y correlación de CVEs, CWE, CAPEC, y noticias sobre ciberseguridad.


---

## 🚀 Objetivo como proyecto open source

- Fomentar la colaboración entre comunidades técnicas y académicas.
- Proveer una infraestructura reutilizable para proyectos de investigación aplicada.
- Crear un ecosistema de plugins y módulos que permita ampliar las capacidades de la plataforma.
- Servir como punto de partida para iniciativas públicas o ciudadanas de análisis e inteligencia de datos.

---

## 🌍 Acceso a la plataforma

Habrá una instancia pública en línea accesible desde web para explorar módulos activos como vivienda o desinformación. También se podrá clonar e instalar localmente o adaptar para nuevos fines.

---

## Definiciones

### **OSINT (Open Source Intelligence)**  

**Definición**:  
El **OSINT** (Inteligencia de Fuentes Abiertas) es una metodología para recopilar, analizar y aprovechar información de **fuentes de acceso público** con el fin de generar conocimiento útil. Se centra en datos disponibles legalmente, sin requerir técnicas intrusivas o ilegales.

#### **Características clave**:  
- **Fuentes**: Redes sociales, sitios web, foros, registros gubernamentales, artículos, metadatos, imágenes, y cualquier recurso público.  
- **Propósito**:  
  - Apoyar investigaciones (periodísticas, policiales, corporativas).  
  - Identificar riesgos de seguridad (fugas de datos, vulnerabilidades).  
  - Analizar tendencias o comportamientos en redes sociales.  
- **Ética**: Se basa en el uso responsable de información pública, respetando la privacidad y leyes locales.  

#### **Ejemplos de aplicaciones**:  
- Periodistas: Verificar datos para reportajes.  
- Equipos de ciberseguridad: Detectar exposiciones de datos sensibles.  
- Empresas: Estudiar a la competencia o proteger su reputación.  

#### **Herramientas asociadas**:  
- Buscadores avanzados (Google Dorking).  
- Shodan (dispositivos IoT expuestos).  
- Maltego (mapeo de relaciones entre datos).  
- theHarvester (recolección de correos y dominios).  

### **Técnicas de Extracción de Datos**  

**Definición**:  
Procesos para obtener, transformar y estructurar información cruda (texto, imágenes, metadatos, etc.) desde fuentes heterogéneas (webs, documentos, PDFs) a formatos útiles (CSV, JSON, bases de datos).  

#### **1. Web Scraping (Extracción de datos de sitios web)**  
- **Propósito**: Automatizar la recolección de datos estructurados desde páginas web.  
- **Herramientas**:  
  - **Scrapy** (framework en Python para scraping avanzado).  
  - **Beautiful Soup** (biblioteca para parsear HTML/XML).  
- **Cómo funciona**:  
  - Identifica patrones en el HTML (etiquetas, clases CSS).  
  - Extrae texto, enlaces, tablas o imágenes.  
  - Almacena los datos en formatos como JSON o CSV. 

### **2. Procesamiento de Documentos**  

**Propósito**: Extraer texto, tablas o metadatos de PDFs, Word, Excel, etc.  

**Herramientas**:  
- **Apache Tika (Java/Python)**: Extracción de contenido y metadatos.  
  ```bash  
  # Usar Tika desde línea de comandos  
  java -jar tika-app.jar --text documento.pdf  
- **APyPDF2 (Python)**: Manipulación básica de PDFs.

### **3. Extracción de Metadatos**  

**Propósito**:Obtener información oculta (autor, GPS, fecha de creación).
**Herramientas**:  
- **ExifTool**: Metadatos en imágenes, PDFs y videos.

## **Procesamiento de Texto y Categorización con NLP/ML**  

### **1. Procesamiento de Texto (NLP)**  

**Propósito**:  
Transformar texto no estructurado en información estructurada (keywords, entidades, temas) para clasificar y priorizar datos en herramientas de inteligencia como **MISP**.  

**Técnicas Clave**:  

#### **A. Preprocesamiento de Texto**  
- **Tokenización**: Dividir texto en palabras o frases.  

#### **B. Extracción de Keywords**  
- **Tokenización**: Dividir texto en palabras o frases. 

##### **B. Extracción de Keywords**  

-TF-IDF (Frecuencia Término-Inverso de Documento): Identifica palabras clave relevantes en un corpus de documentos. 
- RAKE (Rapid Automatic Keyword Extraction): Extrae frases clave basadas en frecuencia y co-ocurrencia.

##### **C. Reconocimiento de Entidades (NER)**  

- Identificar entidades como organizaciones, ubicaciones, o indicadores de compromiso (IOCs).

### **2. Machine Learning para Categorización

**Propósito**: Clasificar automáticamente la información en categorías útiles para inteligencia (ej: "phishing", "malware", "vulnerabilidades").

**Técnicas Clave**: 

##### **A. Aprendizaje Supervisado**

**Clasificación de Texto**: Con modelos como SVM, Random Forest, Redes Neuronales (LSTM, Transformers). Se debe Etiquetar datos manualmente y Entrenar un modelo con embeddings.

##### **B. Aprendizaje No Supervisado**

- *Clustering*: Agrupar documentos similares sin etiquetas previas.
- *Topic Modeling*: Descubrir temas ocultos en documentos (ej: LDA).

> 💡 *Creemos que la inteligencia de datos debe estar al servicio de la sociedad. Este proyecto es nuestra apuesta por una tecnología transparente, abierta y colaborativa.*
