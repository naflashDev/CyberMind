# 🤖 LLM Integrado: Alcance y Uso

Este documento describe el propósito, límites y recomendaciones de uso del **LLM** integrado en CyberMind.

---

## 🎯 Propósito

El LLM actúa como asistente técnico especializado para:

- Explicar y contextualizar **CVE** (Common Vulnerabilities and Exposures)
- Resumir noticias y textos extraídos por los scrapers
- Ayudar con análisis técnicos relacionados con informática y ciberseguridad

> ⚠️ **Nota:** El LLM no sustituye fuentes oficiales ni realiza atribuciones definitivas. Complementa el análisis, pero siempre verifica en fuentes oficiales para decisiones críticas.

---

## 📦 Alcance y limitaciones

| Aspecto | Detalle |
|:---|:---|
| **Dominio** | CVE, vulnerabilidades, mitigaciones, indicadores técnicos, resúmenes de noticias |
| **Datos de entrenamiento** | Solo documentos y noticias scrapeados y procesados por el sistema (outputs/result.json, índices en OpenSearch) |
| **Limitaciones** | No da consejos fuera del ámbito técnico ni debe usarse para decisiones legales sin verificación humana |

---

## 🦙 Modelo utilizado y restricciones

El sistema de IA de CyberMind utiliza un modelo **LLama3** restringido, configurado mediante un archivo **Model file** que limita sus respuestas y comportamiento. La base de conocimiento del modelo está limitada hasta el año **2023** y no incluye información posterior.

> ⚠️ **Importante:** El modelo actual **NO ha sido finetuneado** con los datos extraídos por el sistema. La función de entrenamiento personalizado (R.A.G) se implementará en el futuro, ya que el proceso de diseño e implementación lleva bastante tiempo.

- El modelo responde únicamente sobre temas de ciberseguridad y CVE según las restricciones del Model file.
- No puede responder sobre eventos, vulnerabilidades o noticias posteriores a 2023.
- El R.A.G con datos propios está planificado como mejora futura.
- El archivo JSON para el finetuning **sí se genera** automáticamente (`outputs/finetune_data.jsonl`), pero no se utiliza aún para entrenar el modelo.

---

## 🔗 Endpoints relevantes

| Método | Ruta | Descripción |
|:---:|:---|:---|
| POST | `/llm/query` | Enviar prompt y recibir respuesta |
| GET | `/llm/updater` | Inicia el proceso periódico de actualización de la información para el LLM |
| GET | `/llm/stop-updater` | Detiene el proceso iniciado |

---

## 📝 Buenas prácticas al formular prompts

- Sé específico: incluye identificadores como `CVE-YYYY-NNNN` cuando los tengas
- Pide resúmenes breves si necesitas rapidez: `Resume CVE-2024-4320 en 3 puntos`
- Evita prompts ambiguos o fuera de dominio (por ejemplo, política general no relacionada con vulnerabilidades)

---

## 🖥️ Recomendaciones de infraestructura

- Uso intensivo: se recomienda GPU (NVIDIA/CUDA) para evitar sobrecargas de CPU/memoria
- Sin GPU: controla la concurrencia y desactiva tareas automáticas de finetuning en producción

---

## 🧩 Integración con la UI

- El chat **CyberSentinel** está integrado en la UI principal (`/ui`)
- Desde la UI puedes iniciar el `llm_updater` y ver el historial de interacciones

---

## ⚡ Inicio automático de servicios

Al arrancar `main.py`, la aplicación puede iniciar servicios adicionales (contenedores Docker para OpenSearch/TinyRSS, procesos locales para el LLM) si está habilitado en la configuración (`cfg.ini`, carpeta `Install/`).

---

## 🔒 Privacidad y datos

- El LLM procesa internamente los textos scrapeados; no envía datos a servicios externos por defecto
- Si conectas un proveedor externo (Ollama, OpenAI, etc.), actualiza la documentación y la política de privacidad

---

## 🛠️ Notas operativas

- El `llm_updater` puede ejecutar tareas de actualización periódica (clon de repositorios CVE, construcción de dataset, fine-tuning). Controla su ejecución desde la UI
- En entornos de pruebas/CI desactiva el updater automático para evitar llamadas largas o dependencias externas

---

## ⚙️ Activación/desactivación del LLM por configuración

El uso del LLM en el análisis de código (explicaciones avanzadas de vulnerabilidades) está controlado por el flag `use_ollama` en los archivos `.ini` de la carpeta `src/` (`cfg.ini` o `cfg_services.ini`).

- Si el flag está en `true` en alguno de los archivos, el sistema contactará con el LLM para generar explicaciones.
- Si el flag está en `false` en ambos, la explicación LLM se sustituye por el texto fijo: "LLM desactivado por configuración.".

Esto permite controlar el uso de recursos y la privacidad desde la configuración, sin modificar el código.