
# 🏷️ Extracción de Valores de Datos

## 📝 Text Processor

`text_processor.py` es una utilidad en Python para procesar textos multilingües, detectar el idioma automáticamente y extraer entidades nombradas usando modelos de **spaCy**.

---

## ✨ Características principales

| Funcionalidad | Descripción |
|:---|:---|
| Detección automática de idioma | Utiliza `langdetect` |
| Extracción de entidades nombradas | Basada en `spaCy` |
| Multilingüe | Español, inglés y francés |
| Procesamiento de archivos JSON | Entrada/salida estructurada |
| Resultados ordenados | Por relevancia (número de entidades) |

---

## 🔗 Integración con herramientas de PLN

El procesador es extensible e integrable con herramientas modernas de PLN:

- **spaCy**: reconocimiento de entidades y extracción estructurada
- **Hugging Face Transformers**: clasificación, resumen, análisis de sentimientos
- **LangChain**: cadenas de procesamiento inteligentes con LLMs

---

## 🛠️ Caso de uso típico

1. Obtención de noticias mediante **Scrapy** u otros métodos de scraping
2. Procesamiento del archivo JSON resultante con `text_processor.py`
3. Análisis con **spaCy** para identificar entidades (personas, organizaciones, ubicaciones)
4. Guardado del resultado en un nuevo JSON indexable en **OpenSearch**
5. Consulta por un agente inteligente (ej. con **LangChain**) para responder preguntas, generar informes o automatizar tareas

---

## 📦 Requisitos

- Python 3.7+
- Dependencias:
  ```bash
  pip install spacy langdetect
  python -m spacy download es_core_news_sm
  python -m spacy download en_core_web_sm
  python -m spacy download fr_core_news_sm
  ```

---

## ▶️ Uso

```bash
python text_processor.py input.json output.json
```

---

## 📄 Ejemplo de entrada (`input.json`)

```json
{
    "url": "https://www.industrialdataworks.com/",
    "title": "ICS Vulnerability API",
    "h1": [
      "ICS Vulnerability Data API"
    ],
    "h2": [],
    "h3": [],
    "h4": [],
    "h5": [],
    "h6": [],
    "p": [
      "Subscribe",
      "See Pricing & Options",
      "Download ICS Advisory Project and Industrial Data Works ICS Vulnerabilities Research Report for 2023",
      "16 Critical Infrastructure Sectors",
      "Chemical Sector",
      "Commercial Facilities Sector",
      "Communications Sector",
      "Critical Manufacturing Sector",
      "Dams Sector",
      "Defense Industrial Base Sector",
      "Emergency Services Sector",
      "Energy Sector",
      "Financial Services Sector",
      "Food and Agriculture Sector",
      "Government Facilities Sector",
      "Healthcare and Public Health Sector",
      "Information Technology Sector",
      "Nuclear Reactors, Materials, and Waste Sector",
      "Transportation Systems Sector",
      "Water and Wastewater Systems Sector",
      "About Industrial Data Works",
      "Industrial Data Works is a company that specializes in providing a comprehensive range of services related to industrial control systems (ICS) vulnerability intelligence data. One of their key offerings is the provision of an application programming interface (API) for the ICS Advisory Project (ICS[AP]) data, allowing seamless integration with service provider ICS Security Platforms and corporate customer data visualization applications.",
      "In addition to their API services, Industrial Data Works offers consulting services to help organizations optimize their ICS security and operational efficiency. These services include Network Vulnerability & Threat Analysis Development, where they analyze network vulnerabilities and threats to identify potential risks. They also provide Network Architecture Reviews & Recommendations, assisting clients in enhancing their network infrastructure for better performance and security.",
      "Furthermore, Industrial Data Works conducts Asset Inventory Analysis, which involves assessing and documenting the assets within an industrial system, helping organizations gain a comprehensive understanding of their resources. They also offer Vulnerability Analysis and Patch Management Strategy Development, assisting clients in identifying vulnerabilities within their systems and developing effective strategies to manage and patch them.",
      "Overall, Industrial Data Works aims to provide comprehensive solutions and expertise to support organizations in optimizing their industrial control systems security, efficiency, and integration capabilities.",
      "Products",
      "Services",
      "About",
      "Contact",
      "Privacy PolicyTerms of Service",
      "COPYRIGHT © 2025 INDUSTRIAL DATA WORKS, LLC. ALL RIGHTS RESERVED.For information about how we collect, use, share or otherwise process information about you, please see our privacy policy."
    ]
  }
]

```

### Ejemplo de salida (`output.json`):

```json
  {
  "text": "Industrial Data Works is a company that specializes in providing a comprehensive range of services related to industrial control systems (ICS) vulnerability intelligence data. One of their key offerings is the provision of an application programming interface (API) for the ICS Advisory Project (ICS[AP]) data, allowing seamless integration with service provider ICS Security Platforms and corporate customer data visualization applications.",
  "language": "en",
  "tags": [
    ["Industrial Data Works", "ORG"],
    ["industrial control systems", "ORG"],
    ["ICS", "ORG"],
    ["application programming interface", "ORG"],
    ["ICS Advisory Project", "ORG"],
    ["service provider ICS Security Platforms", "ORG"],
    ["corporate customer data visualization applications", "ORG"]
  ],
  "relevance": 7
]
```