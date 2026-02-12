
# 🗄️ Bases de Datos en CyberMind

Este capítulo describe las bases de datos utilizadas en el sistema y su propósito dentro del flujo de recolección y gestión de información.

---

## 🔎 OpenSearch

OpenSearch se utiliza para **almacenar los datos scrapeados desde la web**. Permite búsquedas rápidas y eficientes sobre textos y metadatos recolectados.

**Se almacena información proveniente de:**

- Técnicas de scraping
- Consultas de Google Dorking
- Fuentes RSS externas no gestionadas por TinyRSS

> 📈 **Ventaja:** Búsqueda semántica y filtrado avanzado sobre grandes volúmenes de datos no estructurados.

---

## 🐘 PostgreSQL

PostgreSQL se emplea para **almacenar la información procedente de TinyRSS**. Es el repositorio estructurado de todas las fuentes y artículos gestionados por el sistema TinyRSS.

**Se registran:**

- Fuentes RSS configuradas en TinyRSS
- Artículos obtenidos desde cada feed
- Metadatos asociados a los artículos

> 🗃️ **Ventaja:** Permite consultas estructuradas, relaciones y gestión eficiente de feeds y artículos.

---

## 🔑 SQLite (Servicio de Hashing)

El servicio de hashing utiliza una base de datos **SQLite** para almacenar y gestionar los hashes generados y sus metadatos asociados. Esta base de datos ligera permite una gestión eficiente y local de los valores hash, facilitando operaciones rápidas y persistencia sin requerir un servidor de base de datos externo.

**Se almacena información como:**

- Hashes calculados a partir de contraseñas u otros valores
- Salts y parámetros de generación
- Tiempos de creación y uso
- Estado de verificación o uso

> 🔒 **Ventaja:** Al ser embebida, SQLite simplifica la gestión y despliegue del servicio de hashing, manteniendo la seguridad y la persistencia de los datos críticos sin dependencias externas.
