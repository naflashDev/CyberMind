

# 🔎 Instalación y configuración de OpenSearch para CyberMind

Guía recomendada para desplegar **OpenSearch** y **OpenSearch Dashboards** usando Docker Compose.

---

## 🐳 Despliegue con Docker Compose (recomendado)

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

4. Accede a OpenSearch en [http://localhost:9200](http://localhost:9200) y a Dashboards en [http://localhost:5601](http://localhost:5601)

5. Para detener y eliminar contenedores:

	```bash
	docker compose -f opensearch-compose.yml down
	```

---

## 📊 Consultar índices y datos (curl)

Ver los índices:

```bash
curl -X GET "http://localhost:9200/_cat/indices?v"
```

Ver documentos del índice `scrapy_documents`:

```bash
curl -X GET "http://localhost:9200/scrapy_documents/_search?pretty"
```

Ver documentos del índice `spacy_documents`:

```bash
curl -X GET "http://localhost:9200/spacy_documents/_search?pretty"
```

---

## 📈 Dashboards

Accede a [http://localhost:5601](http://localhost:5601) para crear patrones de índice y explorar datos en Discover.

---

## 🛠️ Alternativa: instalación manual

Si necesitas instalar OpenSearch manualmente en Linux, puedes descargar y ejecutar OpenSearch desde tarball. Solo recomendado para entornos sin Docker.

> Los archivos de configuración `opensearch.yml` y `opensearch_dashboards.yml` se encuentran en la carpeta `Install/` si quieres revisar o adaptar ajustes.
#
