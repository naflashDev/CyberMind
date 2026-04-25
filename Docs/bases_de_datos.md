
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

---

## 🟣 Chroma (vectorstore) — almacenamiento de embeddings

Chroma (Chromadb) se usa en el proyecto como **vectorstore** para almacenar embeddings y metadatos asociados a documentos y mensajes, habilitando la capa de recuperación necesaria para R.A.G. (Retrieval-Augmented Generation).

- Estructura básica: Chroma organiza los datos en **colecciones**. Cada documento guardado en una colección incluye:
	- **id**: identificador único (por ejemplo `finetune-<hash>` o `conv-<id>-msg-<id>`).
	- **embedding**: el vector numérico que representa el contenido (float array).
	- **document/text**: el texto original o la concatenación instruction+input+output usada en pipelines de finetune.
	- **metadata**: un diccionario con atributos libres (por ejemplo `source`, `timestamp`, `conversation_id`, `role`, `file_path`).

- Persistencia y modos de uso:
	- Chroma puede operar **en memoria** o con persistencia en disco (directorio de persistencia). En este proyecto la ingestión por defecto intenta usar un cliente Chroma persistente cuando está disponible.
	- El método `upsert` se utiliza para insertar o actualizar documentos por `id` (evita duplicados si se repite la misma fuente).

- Prácticas usadas en CyberMind:
	- Al generar el JSONL de finetune (`outputs/finetune_data.jsonl`) cada registro se transforma en un texto combinado (instruction + input + output) y se calcula un `doc_id` estable (SHA256 hash) antes de `upsert` en la colección.
	- Los mensajes de conversación también se pueden upsertar con `doc_id` tipo `conv-<conv_id>-msg-<msg_id>` para que sean recuperables por contexto.
	- El campo `metadata.source` se rellena para facilitar trazabilidad y exposición en la API (se muestra en `retrieved` al consultar `/llm/query`).

- Recuperación y búsqueda:
	- Las búsquedas se realizan por similitud (top-k) sobre el espacio de embeddings; el cliente devuelve los textos, metadatos y puntajes de similitud.
	- Al recuperar documentos, el sistema concatena fragmentos y los inyecta en el prompt como contexto adicional antes de llamar al LLM.

- Consideraciones operativas:
	- Dependencias: para usar Chroma se recomienda instalar `chromadb` y un adaptador de embeddings (por ejemplo el adaptador a Ollama si se usa `ollama` localmente).
	- Recursos: la indexación y la búsqueda son intensivas en I/O y memoria; en despliegues con volumen alto conviene provisionar persistencia rápida (SSD) y suficiente RAM.
	- Chunking: para documentos largos se recomienda fragmentarlos (chunking) antes de generar embeddings para mejorar la recuperación de fragmentos relevantes.

> Ejemplo (resumen): al ingestar `outputs/finetune_data.jsonl` el flujo crea `doc_id` estables, calcula embeddings (si está configurado el adaptador), y hace `_chroma_client.upsert_document(doc_id=..., text=..., metadata={...})` para que los registros sean recuperables por R.A.G.
