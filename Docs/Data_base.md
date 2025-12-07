# Bases de datos

Este capítulo describe las bases de datos utilizadas en el sistema y su propósito dentro del flujo de recolección y gestión de información.

---

## OpenSearch

OpenSearch se utiliza como base de datos para **almacenar los datos scrapeados desde la web**.  
En ella se guarda la información recopilada mediante:

- Técnicas de scraping.
- Consultas de Google Dorking.
- Fuentes RSS externas no gestionadas por TinyRSS.

Su función principal es permitir búsquedas rápidas y eficientes sobre los textos y metadatos recolectados.

---

## PostgreSQL

PostgreSQL se emplea como base de datos para **almacenar la información procedente de TinyRSS**.  
Aquí se registran:

- Las fuentes RSS configuradas en TinyRSS.
- Los artículos obtenidos desde cada feed.
- Los metadatos asociados a los artículos.

Esta base de datos sirve como repositorio estructurado para toda la información gestionada por el sistema TinyRSS.

---
