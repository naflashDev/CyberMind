
# Instalación y configuración de OpenSearch para CyberMind (recomendado: Docker Compose)

Esta guía refleja el método recomendado de despliegue para **CyberMind**: usar `docker compose` para levantar OpenSearch y OpenSearch Dashboards. Hay un fichero preparado en `Install/opensearch-compose.yml` y los archivos de configuración (`opensearch.yml` y `opensearch_dashboards.yml`) en la carpeta `Install/`.

## Usar Docker Compose (recomendado)

1. Abre una terminal en la raíz del proyecto y entra en la carpeta `Install`:

```bash
cd Install
```

2. Levanta OpenSearch y Dashboards en background:

```bash
docker compose -f opensearch-compose.yml up -d
```

3. Comprueba que los servicios están arriba:

```bash
docker compose -f opensearch-compose.yml ps
```

4. Accede a OpenSearch en `http://localhost:9200` y a Dashboards en `http://localhost:5601`.

5. Para detener y eliminar contenedores:

```bash
docker compose -f opensearch-compose.yml down
```

## Ver índices y datos (curl)

Ver los índices:

```bash
curl -X GET "http://localhost:9200/_cat/indices?v"
```

Ver los documentos del índice `scrapy_documents`:

```bash
curl -X GET "http://localhost:9200/scrapy_documents/_search?pretty"
```

Ver los documentos del índice `spacy_documents`:

```bash
curl -X GET "http://localhost:9200/spacy_documents/_search?pretty"
```

## Dashboards

Una vez OpenSearch Dashboards esté arriba, accede a `http://localhost:5601`. Desde la interfaz puedes crear patrones de índice (Index Patterns) y explorar datos en Discover.

## Alternativa: instalación manual

Si por alguna razón necesitas instalar OpenSearch de forma manual en Linux, la versión anterior del proyecto incluía pasos para descargar y ejecutar OpenSearch desde tarball. Es una opción válida para entornos sin Docker, pero no es la ruta recomendada para desarrollo.

> Los archivos de configuración `opensearch.yml` y `opensearch_dashboards.yml` se encuentran en la carpeta `Install/` si quieres revisar o adaptar ajustes.
#
