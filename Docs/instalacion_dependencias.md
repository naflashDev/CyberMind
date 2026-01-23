
# 🐍 Configuración del Entorno de Desarrollo Python

El uso de **entornos virtuales (`env`)** es fundamental para la gestión de dependencias, asegurando que cada proyecto tenga su propio conjunto de librerías sin interferir con otros proyectos o el sistema operativo.

---

## ⌨️ Comandos esenciales

| Descripción | Sistema Operativo | Comando |
|:---|:---|:---|
| Crear entorno virtual | Todos | `python -m venv env` |
| Activar (Windows) | Windows | `.\env\Scripts\activate` |
| Activar (Linux/macOS) | Linux/macOS | `source env/bin/activate` |
| Generar requirements.txt | Todos | `pip freeze > requirements.txt` |
| Instalar dependencias | Todos | `pip install -r requirements.txt` |
| Desactivar entorno | Todos | `deactivate` |

---

## 📄 Notas sobre requirements

El fichero `requirements.txt` se encuentra en el directorio raíz del proyecto. Asegúrate de actualizarlo tras instalar nuevas dependencias.

---

## 🛠️ Requisitos adicionales

- Python 3.10+ recomendado (el proyecto se prueba con Python 3.12)
- Docker y Docker Compose para levantar OpenSearch y TinyRSS (si usas los contenedores)

**Instalación rápida de Docker:**

Consulta la guía oficial: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

---

## 🚀 Levantar servicios con Docker Compose

Desde la carpeta `Install/` puedes levantar los servicios necesarios:

```bash
cd Install
docker compose -f opensearch-compose.yml up -d
docker compose -f tinytinyrss.yml up -d
```

---

## ⚡ Notas sobre rendimiento y LLM

- Uso intensivo del LLM: se recomienda GPU para evitar saturar CPU/RAM. En instalaciones pequeñas o pruebas, es posible usar CPU (menor rendimiento).

---

## 🔄 Inicio automático de servicios

La aplicación principal (`main.py`) puede comprobar e iniciar servicios configurados (contenedores Docker, procesos locales del LLM) si la opción está habilitada en la configuración (`cfg.ini`, carpeta `Install/`).


