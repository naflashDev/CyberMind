<div align="center">

# 🛡️ CyberMind

**Plataforma modular de análisis y monitorización de ciberseguridad IT/OT con IA, scraping, dashboards y orquestación automatizada.**

---

[![Python](https://img.shields.io/badge/Python-3.12+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![OpenSearch](https://img.shields.io/badge/OpenSearch-0057B8?style=for-the-badge&logo=opensearch&logoColor=white)](https://opensearch.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![Security](https://img.shields.io/badge/Security-By%20Design-4ECDC4?style=for-the-badge)](#-seguridad)
[![LLM](https://img.shields.io/badge/LLM-CyberSentinel-7B68EE?style=for-the-badge)](#-ia)

</div>

**CyberMind** es una plataforma modular, automatizada y de código abierto para la auditoría, análisis, monitorización y automatización de tareas de ciberseguridad en entornos **IT** y **OT**. Va mucho más allá de la simple recolección de datos: permite realizar auditorías técnicas, análisis de vulnerabilidades, orquestación de flujos de trabajo, generación de dashboards, integración de IA y procesamiento avanzado de información.

> 🎯 **Objetivo:** Proveer una solución integral y flexible para la gestión de inteligencia, auditoría y automatización en ciberseguridad, facilitando el acceso a datos estructurados y procesados, la correlación de eventos y la toma de decisiones informada. Promueve la transparencia, la colaboración abierta y el uso de metodologías de inteligencia y automatización.

---

## 🚀 Quick Start

### 🐳 Con Docker Compose (Recomendado)
```bash
# 1. Clonar el repositorio

# 2. Instalar dependencias

cd CyberMind
python -m venv env
source env/bin/activate  # En Windows: .\env\Scripts\activate
pip install -r requirements.txt

# 3.Levantar servicios (Opcional, ya que el programa hace el compose automaticamente)

cd Install
docker compose -f opensearch-compose.yml up -d
docker compose -f tinytinyrss.yml up -d

# 4.Arrancar la aplicacion

cd ..
cd src
python main.py
```

- 🌐 UI: [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui)
- 📡 API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📊 Dashboards: [http://localhost:5601](http://localhost:5601)

---

## 🛠️ Stack Tecnológico

| Componente      | Descripción / Uso principal                  |
|-----------------|---------------------------------------------|
| 🐍 Python 3.12+ | Backend principal, scripts y automatización |
| ⚡ FastAPI      | API REST y servidor web                      |
| 🧠 SpaCy       | Procesamiento NLP, extracción de entidades   |
| 📰 Scrapy       | Scraping de noticias, feeds y alertas        |
| 🐘 PostgreSQL  | Base de datos estructurada                   |
| 🔎 OpenSearch  | Búsqueda semántica y dashboards              |
| 🐳 Docker      | Orquestación de servicios y contenedores     |
| 🤖 LLM         | Chat IA especializado en CVE y OT/IT         |
| 🦾 Workers     | Orquestación de tareas y procesos            |
| 🛡️ Seguridad  | Validación, gestión de secretos, SAST        |
| ⚙️ CI/CD      | Workflows automáticos con GitHub Actions      |

---

## ✨ Funcionalidades Principales

- 🔗 Integración multifuente: RSS, Google Alerts, Google Dorking, APIs públicas
- 🧠 Procesamiento semántico: keywords, NER, sentimiento, embeddings
- 📦 Almacenamiento híbrido: OpenSearch y PostgreSQL
- 📊 Dashboards abiertos: OpenSearch Dashboards, Grafana, Chartbrew
- 🤖 LLM CyberSentinel: consulta y resumen de CVEs/noticias OT/IT
- 🦾 Orquestador ligero: workers y tareas automatizadas
- 🛡️ Security by Design: validación, gestión de secretos, CI/CD
- 📝 Generación de JSON para finetune de LLM
- 🚀 Expansión continua: nuevos módulos y servicios en desarrollo

---

## 🧩 Documentación y enlaces

- 📚 Documentación principal: [Docs/Indice.md](Docs/Indice.md)
- 🔗 Endpoints API: [Docs/api_endpoints.md](Docs/api_endpoints.md)
- 🤖 LLM integrado: [Docs/llm.md](Docs/llm.md)
- 🛠️ Instalación dependencias: [Docs/instalacion_dependencias.md](Docs/instalacion_dependencias.md)
- ⚙️ Workflows CI/CD: [Docs/Workflows.md](Docs/Workflows.md)
- 📝 Registro de cambios: [Docs/ChangeLog.md](Docs/ChangeLog.md)

---

## 🤖 IA y modelo LLM

La IA integrada en CyberMind utiliza un modelo **LLama3** restringido, configurado mediante un archivo **Model file** que limita sus respuestas y comportamiento. La base de conocimiento del modelo está limitada hasta el año **2023** y no incluye información posterior.

> ⚠️ **Importante:** El modelo actual **NO ha sido finetuneado** con los datos extraídos por el sistema. La función de entrenamiento personalizado (finetuning) se implementará en el futuro, ya que el proceso es altamente demandante en recursos y tiempo.

- El modelo responde únicamente sobre temas de ciberseguridad y CVE según las restricciones del Model file.
- No puede responder sobre eventos, vulnerabilidades o noticias posteriores a 2023.
- El finetuning con datos propios está planificado como mejora futura.
- El archivo JSON para el finetuning **sí se genera** automáticamente (outputs/finetune_data.jsonl), pero no se utiliza aún para entrenar el modelo.

---


## 🏗️ Estructura de directorios del proyecto

```plaintext
CyberMind/
├── AGENTS.md
├── LICENSE
├── README.md
├── requirements.txt
├── dev-requirements.txt
├── Docs/
│   ├── Indice.md
│   ├── ChangeLog.md
│   ├── api_endpoints.md
│   ├── home.md
│   ├── llm.md
│   ├── instalacion_dependencias.md
│   ├── opensearch_install.md
│   ├── tiny_rss_install.md
│   ├── ...
├── Install/
│   ├── opensearch-compose.yml
│   ├── tinytinyrss.yml
│   ├── stack.env
│   ├── ...
├── src/
│   ├── main.py
│   ├── cfg.ini
│   ├── cfg_services.ini
│   ├── app/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── services/
│   │   ├── ui/
│   │   ├── utils/
│   │   └── ...
│   ├── data/
│   │   ├── cve_list.json
│   │   ├── feeds/
│   │   ├── outputs/
│   │   └── ...
│   └── ...
├── tests/
│   ├── controllers/
│   ├── integration/
│   ├── services/
│   ├── unit/
│   ├── utils/
│   └── ...
├── tools/
│   ├── audit_fstrings.py
│   ├── scan_injection.py
│   ├── outputs/
│   ├── scripts/
│   └── ...
└── env/
    ├── Scripts/
    ├── Lib/
    ├── Include/
    └── ...
```

| Elemento                | Descripción breve                                                                 |
|-------------------------|---------------------------------------------------------------------------------|
| AGENTS.md               | Normas y estándares para el agente IA y desarrollo del proyecto                   |
| LICENSE                 | Licencia privativa: uso personal, educativo o investigación. Derivados solo con permiso. |
| README.md               | Documentación principal y guía rápida                                            |
| requirements.txt        | Dependencias principales del proyecto                                           |
| dev-requirements.txt    | Dependencias para desarrollo y testing                                          |
| Docs/                   | Documentación técnica, API, instalación, workflows y registro de cambios         |
| Install/                | Archivos de configuración y orquestación de servicios (Docker Compose, env)      |
| src/                    | Código fuente principal del proyecto                                            |
| src/main.py             | Punto de entrada de la API y la UI                                              |
| src/app/                | Módulos de la aplicación: controladores, servicios, UI, utilidades              |
| src/data/               | Datos, feeds, resultados de scraping y procesamiento                             |
| tests/                  | Pruebas unitarias, de integración y de servicios                                |
| tools/                  | Scripts y utilidades para auditoría, análisis y automatización                   |
| env/                    | Entorno virtual Python para aislar dependencias                                 |

---

## 👨‍💻 Sobre el Creador

### Ignacio Fernández
*Software Developer | Lifelong Learner & Tech Enthusiast*

- 🐙 **GitHub**: [@naflashDev](https://github.com/naflashDev)
- 📧 **Email**: [Contactar via GitHub Issues](https://github.com/naflashDev/CyberMind/issues)


## 📄 Licencia

Este proyecto está protegido por una **licencia privativa personalizada**:

- El uso está permitido únicamente para fines personales, educativos o de investigación.
- Se permite la creación de versiones derivadas solo para uso personal, educativo o de investigación.
- Queda prohibida la redistribución, publicación o uso comercial sin autorización expresa y por escrito del titular.
- Toda versión derivada debe incluir un aviso visible de modificación y mantener el texto de licencia.
- Para más detalles, consulta el archivo [LICENSE](LICENSE).

## 🤝 Contribuciones y Soporte

### 🐛 Reportar Issues
¿Encontraste un bug o tienes una sugerencia? 

👉 **[Crear una Issue en GitHub](https://github.com/naflashDev/CyberMind/issues/new)**

Por favor incluye:
- 📝 Descripción detallada del problema
- 🔄 Pasos para reproducir
- 💻 Información del entorno (OS, Python version, Docker version)
- 📸 Screenshots si es relevante

### 💡 Contribuir al Proyecto

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. **Commit** tus cambios (`git commit -m 'Add amazing feature'`)
4. **Push** a la rama (`git push origin feature/amazing-feature`)
5. **Abre** un Pull Request

---
<div align="center">
<b>CyberMind &copy; 2026</b>
</div>

---

