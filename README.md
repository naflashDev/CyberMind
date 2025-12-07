# CyberMind

# Proyecto CyberMind – Plataforma Abierta de Análisis de Información

**CyberMind** es una plataforma modular, automatizada y de código abierto para la recolección, análisis y visualización de información relevante sobre Las vulnerabilidades IT y OT (Tecnologías de la Información y Tecnologías de Operación). Su objetivo es facilitar el acceso a datos estructurados y procesados a partir de fuentes públicas, con enfoque en la transparencia, la colaboración abierta y el uso de metodologías de inteligencia.

El proyecto está orientado tanto a investigadores, periodistas de datos y analistas, como a desarrolladores interesados en contribuir con nuevas funcionalidades y dominios de análisis.

Documentación principal y enlaces rápidos.


## Documentación (Docs)
- Documentacion del proyecto: [Documentacion](Docs/Indice.md)

## Ejecucion programa
-Iniciar entorno virtual comando [Documentacion](Docs/instalacion_dependencias.md)

-Tener arrancado tanto el docker de tiny como el opensearch [Documentacion](Docs/task.md)

-Ejecutar main.py dentro de Scraping_Web/src/main.py

-Podemos aparte de la ejecucion automatica del programa realizar diferentes acciones desde [Fastapi](http://127.0.0.1:8000/docs)

## Visualización de los datos

-Para visualizar los datos scrapeados podemos observar el archivo [Result.json] del directorio [Outputs]

-Para visualizar los datos procesados con spacy podemos observar el archivo [Labels_Result.json] del directorio[Outputs]

-Para visualizar los datos almacenados en la BBDD [Opensearch] desde wsl usaremos los siguientes comandos.
    
Ver los indices

```bash
curl -X GET "http://localhost:9200/_cat/indices?v"
```

Ver el indice de scrapy_documents

```bash
curl -X GET "http://localhost:9200/scrapy_documents/_search?pretty"
```

Ver el indice de spacy_documents

```bash
curl -X GET "http://localhost:9200/spacy_documents/_search?pretty"
```

-Para visualizar los datos almacenados en la BBDD [Opensearch] desde el DashBoard accederemos a la siguiente web si el dhasboard esta levantado [DashBoard](http://localhost:5601/).
