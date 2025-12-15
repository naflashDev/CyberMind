++"""markdown
# LLM integrado (alcance y uso)

Este documento describe el propósito, límites y recomendaciones de uso del LLM integrado en CyberMind.

## Propósito

El LLM sirve como asistente técnico especializado para:  
- Explicar y contextualizar **CVE** (Common Vulnerabilities and Exposures).  
- Resumir noticias y textos extraídos por los scrapers del proyecto.  
- Ayudar con análisis técnicos relacionados con **informática** y **ciberseguridad**.

El objetivo no es sustituir fuentes oficiales ni realizar atribuciones definitivas: el LLM debe complementarse con consultas a las fuentes (CVE databases, repositorios oficiales) cuando se requiera precisión legal o técnica crítica.

## Alcance y limitaciones

- Dominio: CVE, vulnerabilidades, mitigaciones, indicadores técnicos, resúmenes de noticias sobre ciberseguridad.
- Datos de entrenamiento: cuando el LLM usa datos del sistema, se limita a los documentos y noticias que el proyecto ha scrapeado y procesado (outputs/result.json, índices en OpenSearch).  
- No proporciona consejos fuera del ámbito técnico ni se debe usar para decisiones legales o de cumplimiento sin verificación humana.

## Endpoints relevantes

- `POST /llm/query` — Enviar prompt y recibir respuesta.  
- `GET /llm/updater` — Inicia el proceso periódco que actualiza los datos/finetune del LLM (si está habilitado).  
- `GET /llm/stop-updater` — Detiene el proceso iniciado.

## Buenas prácticas al formular prompts

- Sé específico: incluye identificadores como `CVE-YYYY-NNNN` cuando los tengas.  
- Pide resúmenes breves si necesitas rapidez: `Resume CVE-2024-4320 en 3 puntos`.  
- Evita prompts ambiguos o fuera de dominio (por ejemplo, política general no relacionada con vulnerabilidades).

## Recomendaciones de infraestructura

- Si vas a usar el LLM de forma intensiva (muchas consultas concurrentes, tareas de fine-tuning o procesamiento de gran volumen), se recomienda un equipo con GPU (NVIDIA o compatibilidad CUDA) para evitar sobrecargas de CPU y memoria.
- En entornos sin GPU, controla la concurrencia y desactiva tareas automáticas de finetuning en producción para evitar saturar la máquina.

## Integración con la UI

- El chat **CyberSentinel** está integrado en la UI principal (`/ui`) y facilita consultas interactivas. Desde la UI puedes iniciar el `llm_updater` y ver el historial de interacciones.

## Inicio automático de servicios

- Al arrancar `main.py` la aplicación puede iniciar/comprobar servicios adicionales configurados (contenedores Docker para OpenSearch/TinyRSS, procesos locales para el LLM) si esa opción está habilitada en la configuración. Revisa `cfg.ini` y la carpeta `Install/` para ajustar el comportamiento.

## Privacidad y datos

- El LLM procesa internamente los textos scrapeados; no envía datos a servicios externos por defecto (revisa la configuración del conector si usas Ollama, OpenAI u otro servicio).  
- Si conectas un proveedor externo, actualiza la documentación y la política de privacidad del despliegue.

## Notas operativas

- El `llm_updater` puede ejecutar tareas de actualización periódica (clon de repositorios CVE, construcción de dataset, fine-tuning) — controlar su ejecución desde la UI.  
- En entornos de pruebas/CI desactiva el updater automático para evitar llamadas largas o dependencias externas.

Si quieres que añada ejemplos de prompts y respuestas, o snippets para integrar con Python/CLI, dime qué formato prefieres.
"""