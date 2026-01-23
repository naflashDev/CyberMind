
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
