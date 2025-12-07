# Guía de instalación y configuración de OpenSearch 2.12.0 en Linux

## 1. Descargar OpenSearch

Ejecuta el siguiente comando para descargar la versión **2.12.0 para
Linux x64**:

``` bash
curl -O https://artifacts.opensearch.org/releases/bundle/opensearch/2.12.0/opensearch-2.12.0-linux-x64.tar.gz
```

------------------------------------------------------------------------

## 2. Descomprimir el archivo

``` bash
tar -xzf opensearch-2.12.0-linux-x64.tar.gz
```

------------------------------------------------------------------------

## 3. Entrar en la carpeta descomprimida

``` bash
cd opensearch-2.12.0
```

------------------------------------------------------------------------

## 4. Editar el archivo `opensearch.yml`

``` bash
nano config/opensearch.yml
```

Pega la siguiente configuración dentro del archivo:

``` yaml
# ======================== OpenSearch Configuration =========================
#
# NOTE: OpenSearch comes with reasonable defaults for most settings.
#       Before you set out to tweak and tune the configuration, make sure you
#       understand what are you trying to accomplish and the consequences.
#
# The primary way of configuring a node is via this file. This template lists
# the most important settings you may want to configure for a production cluster.
#
# Please consult the documentation for further information on configuration options:
# https://www.opensearch.org
#
# ---------------------------------- Cluster -----------------------------------
#
cluster.name: opensearch-cluster
#
# ------------------------------------ Node ------------------------------------
#
node.name: node-1
#
# Add custom attributes to the node:
#
#node.attr.rack: r1
#
# ----------------------------------- Paths ------------------------------------
#
#path.data: /path/to/data
#path.logs: /path/to/logs
#
# ----------------------------------- Memory -----------------------------------
#
bootstrap.memory_lock: true
#
# ---------------------------------- Network -----------------------------------
#
network.host: 0.0.0.0
http.port: 9200
#
# --------------------------------- Discovery ----------------------------------
#
discovery.type: single-node
#
# ---------------------------------- Gateway -----------------------------------
#
#gateway.recover_after_nodes: 3
#
# ---------------------------------- Various -----------------------------------
#
action.destructive_requires_name: true
#
# ---------------------------------- Security -----------------------------------
#
plugins.security.disabled: true

```
> El archivo necesario (`opensearch.yml`) se encuentran en la carpeta `install`.
------------------------------------------------------------------------

## 5. Ejecutar OpenSearch

``` bash
./bin/opensearch
```

## 6.Visualizar datos

-Abrimos otra ventana de WSL

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


## 7. Ver en DashBoard (Opcional)

1. Abre wsl y descarga con el siguiente comando el archivo de la url:

```bash
wget https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/2.9.0/opensearch-dashboards-2.9.0-linux-x64.tar.gz

```

2. Descomprimir archivo y acceder a la carpeta:

```bash
tar -xzf opensearch-dashboards-2.9.0-linux-x64.tar.gz
cd opensearch-dashboards-2.9.0/
```

3. Editar el fichero yml con un editor de codigo:

```bash
nano config/opensearch_dashboards.yml
```

4. Pegar esta configuracion en el fichero yml

```yaml
# URL de tu OpenSearch
opensearch.hosts: ["http://localhost:9200"]
opensearch.ssl.verificationMode: none   # desactiva verificación de certificados si es self-signed

# Usuario y contraseña de OpenSearch
opensearch.username: "kibanaserver"
opensearch.password: "kibanaserver"

# Multitenancy
opensearch_security.multitenancy.enabled: true
opensearch_security.multitenancy.tenants.preferred: [Private, Global]

# Roles de solo lectura
opensearch_security.readonly_mode.roles: [kibana_read_only]

# Cookies seguras (false si no usas HTTPS en Dashboards)
opensearch_security.cookie.secure: false

# Puerto y host de Dashboards
server.host: "0.0.0.0"

#Security
opensearch_security.enabled: false
opensearch.requestHeadersAllowlist: []  # opcional
```

> El archivo necesario (`opensearch_dashboards.yml`) se encuentra en la carpeta `install`.

5. Ejecutar DashBoard

``` bash
./bin/opensearch-dashboards
```
6. Accedemos desde el navegador a la siguiente web [DashBoard](http://localhost:5601/).

7. Configurar index para visualizar los datos

Configurar un índice en Dashboards

1. Abre tu **OpenSearch Dashboards** en el navegador.  
2. Ve a **Stack Management → Index Patterns**.  
3. Haz clic en **Create index pattern**.  
4. Escribe el nombre del índice que quieres visualizar  
   - Puedes usar comodines, por ejemplo: `scrapy*`  
5. Haz clic en **Create index pattern**.  

Ahora Dashboards “conoce” tu índice y puedes explorarlo.

---

Explorar datos

1. Ve a **Discover** en Dashboards.  
2. Selecciona el **Index Pattern** que acabas de crear.  
3. Verás los documentos de tu índice. Puedes:
   - Filtrar  
   - Ordenar  
   - Buscar por campos específicos  

---

Crear visualizaciones

1. Ve a **Visualize Library → Create visualization**.  
2. Selecciona el tipo de gráfico (bar, line, pie, etc.).  
3. Escoge el **índice** y los **campos** que quieres mostrar.  
4. Guarda la visualización y agrégala a un **Dashboard** para ver todos tus datos juntos.
