# 🐍 Configuración del Entorno de Desarrollo Python

El uso de **Entornos Virtuales (`env`)** es fundamental para la gestión de dependencias, asegurando que cada proyecto tenga su propio conjunto de librerías sin interferir con otros proyectos o el sistema operativo.

---
## ⌨️ Referencia Rápida de Comandos Esenciales

| Descripción | Sistema Operativo | Comando |
| :--- | :--- | :--- |
| **Crear Entorno Virtual** | Todos | `python -m venv env` |
| **Activar (Windows)** | Windows | `.\env\Scripts\activate` |
| **Activar (Linux/macOS)** | Linux/macOS | `source env/bin/activate` |
| **Generar requirements.txt** | Todos | `pip freeze > requirements.txt` |
| **Instalar Dependencias** | Todos | `pip install -r requirements.txt` |
| **Desactivar Entorno** | Todos | `deactivate` |

## El fichero requiremnts se haya en el directorio Scraping_web para que se tenga en cuenta a la hora de ejecutar la instalacion de dependencias

## Requisitos adicionales
- Python 3.10+ recomendado (el proyecto se prueba con Python 3.12).
- Docker y Docker Compose para levantar OpenSearch y TinyRSS (si usas los contenedores).

Instalación rápida de Docker (Linux/Windows/macOS): revisa la guía oficial en https://docs.docker.com/get-docker/

Una vez Docker esté instalado, puedes levantar los servicios con los `docker compose` en la carpeta `Install/`:

```bash
cd Install
docker compose -f opensearch-compose.yml up -d
docker compose -f tinytinyrss.yml up -d
```

## Notas sobre rendimiento y LLM

- Si vas a usar el LLM integrado de forma intensiva (muchas consultas, finetuning), se recomienda disponer de GPU para evitar saturar CPU/RAM. Para instalaciones pequeñas o pruebas es posible usar CPU, pero con menor rendimiento.

## Inicio automático de servicios desde la aplicación

- La aplicación principal (`main.py`) puede comprobar e iniciar servicios configurados (contenedores Docker, procesos locales del LLM) si la opción está habilitada en la configuración. Revisa `cfg.ini` y la carpeta `Install/` para controlar este comportamiento.


