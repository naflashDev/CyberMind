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

