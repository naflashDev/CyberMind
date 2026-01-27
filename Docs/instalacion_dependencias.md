
## 🔑 Variables de entorno y credenciales

CyberMind utiliza un archivo `.env` en la raíz del proyecto para gestionar credenciales y parámetros sensibles (por ejemplo, acceso a bases de datos). **Nunca subas tu `.env` a repositorios públicos.**

Ejemplo de `.env`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password_segura
POSTGRES_DB=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Al clonar el proyecto, copia `.env.example` a `.env` y personaliza los valores según tu entorno:

```sh
cp .env.example .env
```

El backend carga automáticamente estas variables usando [python-dotenv](https://pypi.org/project/python-dotenv/). Si alguna variable no está definida, la aplicación no podrá conectarse a la base de datos.

> ⚠️ **Seguridad:** Nunca dejes credenciales hardcoded en el código fuente. Usa siempre variables de entorno.

---

## 🧪 Aislamiento de entorno para tests automáticos

Para evitar que los tests modifiquen o lean el archivo `.env` de desarrollo, la suite de tests utiliza un archivo **`.env.test`** dedicado. Este archivo se crea y elimina automáticamente durante la ejecución de los tests, garantizando que:

- Los tests nunca sobrescriben ni leen el `.env` real.
- Las variables de entorno de los tests son independientes y seguras.
- El código de carga de variables (incluyendo `load_dotenv`) prioriza `.env.test` si existe.

Ejemplo de `.env.test`:

```env
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_pass
POSTGRES_DB=test_db
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```


**No es necesario crear manualmente `.env.test`: el fixture de tests lo gestiona automáticamente.**

---

## ▶️ Ejecución de la suite de tests

Para lanzar todos los tests con cobertura y obtener el informe HTML, ejecuta:

```sh
/CyberMind/env/Scripts/python.exe -m pytest --maxfail=3 --durations=20 --tb=short --cov=src --cov-report=html
```

Esto:
- Limita a 3 los fallos antes de detener la ejecución.
- Muestra los 20 tests más lentos.
- Usa un traceback corto para errores.
- Genera un informe de cobertura HTML en `htmlcov/index.html`.

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


