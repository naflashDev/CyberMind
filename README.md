<div align="center">

# 🛡️ CyberMind

**Plataforma modular de análisis y monitorización de ciberseguridad IT/OT con IA, scraping, dashboards y orquestación automatizada.**

---


<div align="center">
    <img src="Docs/images/CyberMindLogo-DEF.png" alt="Logo CyberMind" width="220"/>
</div>

---

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

## 🖼️ Arquitectura de la Plataforma

<div align="center">
    <img src="Docs/images/ArquitecturaCyberMind.png" alt="Arquitectura CyberMind" width="600"/>
    <br/>
    <em>Esquema general de la arquitectura de CyberMind</em>
</div>

---

## 🚀 Quick Start

### 🐳 Con Docker Compose (Recomendado)

> ⚠️ **Importante:** Para usar la app es necesario crear un .env con las variables de entorno necesarias.Puedes clonar el .env.example y renombrarlo como .env y cambiar las variables de entorno por las tuyas. En este .env se almacenan las variables de entorno para la bbdd de tiny rss si quieres usar otros datos como variables debes modificar tambien el fichero stack.env del directorio install, para que al hacerse el compose del docker de tiny tenga las claves que tu especifiques.➡️ [Ver guía detallada](tiny_rss_install.md)

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
- 🛠️ Instalación dependencias: [Docs/instalacion_dependencias.md](Docs/instalacion_dependencias.md)
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
| 🗄️ SQLite     | Base de datos de hashing (hash repository)   |

---

## ✨ Funcionalidades Principales

- 🔗 Integración multifuente: RSS, Google Alerts, Google Dorking, APIs públicas
- 🧠 Procesamiento semántico: keywords, NER, sentimiento, embeddings
- 📦 Almacenamiento híbrido: OpenSearch y PostgreSQL
- 📊 Dashboards abiertos: OpenSearch Dashboards, Grafana, Chartbrew
- 🤖 LLM CyberSentinel: consulta y resumen de CVEs/noticias OT/IT
- 🦾 Orquestador ligero: workers y tareas automatizadas
- 🛡️ Security by Design: validación, gestión de secretos, CI/CD
- 📝 Generación de JSON para finetune/R.A.G (futura implementación) de LLM
- 🚀 Expansión continua: nuevos módulos y servicios en desarrollo

---

## 🧩 Documentación y enlaces

- 📚 Documentación principal: [Docs/Indice.md](Docs/Indice.md)
- 🔗 Endpoints API: [Docs/api_endpoints.md](Docs/api_endpoints.md)
- 🤖 LLM integrado: [Docs/llm.md](Docs/llm.md)
- 🛠️ Instalación dependencias: [Docs/instalacion_dependencias.md](Docs/instalacion_dependencias.md)
- ⚙️ Workflows CI/CD: [Docs/Workflows.md](Docs/Workflows.md)
- 📝 Registro de cambios: [Docs/ChangeLog.md](Docs/ChangeLog.md)
- 📅 Roadmap y estado de próximas implementaciones: [Trello CyberMind](https://trello.com/b/IjdRmwLD/cybermind)
- 🎥 Presentación del proyecto: [Ver presentación en Canva](https://www.canva.com/design/DAHBq7K17zs/PjCMwu3Dj2wg58bleBO-Zg/edit?utm_content=DAHBq7K17zs&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

---

## 🤖 IA y modelo LLM

La IA integrada en CyberMind utiliza un modelo **LLama3** restringido (configurado vía `Model file`) especializado en ciberseguridad. El sistema incorpora ahora un flujo de R.A.G. (Retrieval-Augmented Generation) que permite enriquecer las consultas del LLM con contexto recuperado desde un vectorstore.

- La base técnica: el servicio puede indexar documentos y mensajes en un vectorstore (Chroma/Chromadb) y generar embeddings mediante adaptadores (p. ej. Ollama embedding adapter) cuando están disponibles.
- El archivo de dataset para finetuning se sigue generando automáticamente en `outputs/finetune_data.jsonl` y, cuando el vectorstore está disponible, se ingesta automáticamente para que los documentos sean recuperables.
- Al enviar consultas a `POST /llm/query` el sistema realiza una recuperación de contexto (top-k) y lo añade al prompt antes de llamar al LLM, devolviendo además el campo `retrieved` con las fuentes encontradas.

Comportamiento clave:
- Si el vectorstore (Chroma) y el adaptador de embeddings están presentes, las respuestas usan R.A.G. para aportar evidencia y citas.
- Si no hay vectorstore disponible, el LLM sigue funcionando en modo directo (sin recuperación), y las funcionalidades de ingestión/updater son ignoradas con logging apropiado.
- El proceso de actualización (`/llm/updater`) sincroniza fuentes (p. ej. repositorio de CVE), reconstruye el dataset y, cuando procede, lo ingesta en el vectorstore para que esté disponible en consultas posteriores.

Notas operativas:
- El módulo mantiene la opción de almacenar conversaciones y mensajes en la base de datos; los mensajes pueden upsertarse como vectores al añadirlos mediante la API de conversaciones.
- Recomendado: disponer de un entorno con recursos (CPU/GPU y RAM) adecuados para operaciones intensivas (reindexado y generación de embeddings).

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
│   │   ├── controllers/   # Controladores de rutas y lógica de API
│   │   ├── models/        # Modelos de datos y esquemas
│   │   ├── services/      # Lógica de negocio y servicios
│   │   ├── ui/            # Componentes de interfaz de usuario
│   │   ├── utils/         # Utilidades y funciones auxiliares
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
| src/app/                | Núcleo de la aplicación y submódulos                                            |
| src/app/controllers/    | Controladores de rutas y lógica de API                                          |
| src/app/models/         | Modelos de datos y esquemas                                                     |
| src/app/services/       | Lógica de negocio y servicios                                                   |
| src/app/ui/             | Componentes de interfaz de usuario                                              |
| src/app/utils/          | Utilidades y funciones auxiliares                                               |
| src/data/               | Datos, feeds, resultados de scraping y procesamiento                             |
| tests/                  | Pruebas unitarias, de integración y de servicios                                |
| env/                    | Entorno virtual Python para aislar dependencias                                 |

---

## 🚫 Despliegue

Actualmente, **CyberMind** no se encuentra desplegada como servicio en la nube ni como plataforma pública. Esta decisión responde al objetivo principal del proyecto: ser una herramienta **open source** orientada a la ejecución y experimentación en entornos locales, facilitando la auditoría, el análisis y la automatización de tareas de ciberseguridad de forma autónoma y privada.

El enfoque está en proveer una solución flexible y reutilizable que cada usuario pueda instalar, adaptar y ampliar según sus necesidades, sin depender de servicios externos ni de infraestructuras centralizadas.

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

