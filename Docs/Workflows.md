## Refactorización de tests de servicios LLM y spaCy (enero 2026)

Se han limpiado y estandarizado los tests de la capa services/llm y services/spacy. Cada servicio cuenta ahora con un único archivo de test (por ejemplo, `test_finetune_dataset_builder.py`, `test_script_auto.py`, `test_text_processor.py`), sin fragmentación ni duplicados, con imports ordenados y cabecera documental según las normas del proyecto.
Todos los artefactos de test se generan únicamente en la carpeta `tests/`.
## Refactorización de tests de servicios de scraping (enero 2026)

Se han limpiado y estandarizado los tests de la capa services/scraping. Cada servicio cuenta ahora con un único archivo de test (por ejemplo, `test_feeds_gd.py`, `test_news_gd.py`, etc.), sin fragmentación ni duplicados, con imports ordenados y cabecera documental según las normas del proyecto.
Todos los artefactos de test se generan únicamente en la carpeta `tests/`.
## Refactorización de tests de controladores (enero 2026)

Se han limpiado y estandarizado los tests de la capa controllers/routes. Cada controlador cuenta ahora con un único archivo de test (por ejemplo, `test_network_analysis_controller.py`, `test_scrapy_news_controller.py`, etc.), sin fragmentación ni duplicados, con imports ordenados y cabecera documental según las normas del proyecto.
Todos los artefactos de test se generan únicamente en la carpeta `tests/`.
## Refactorización de tests de utilidades (enero 2026)


Se ha completado la refactorización de los tests de los módulos de utilidades:

- Todos los tests de worker_control, utils y run_services están correctamente agrupados y alineados con la estructura del proyecto.
- Los imports están ordenados y situados al inicio de cada archivo.
- Los tests temporales solo crean archivos dentro de la carpeta de tests.
- Se eliminaron fragmentaciones y duplicados.

Esta mejora facilita el mantenimiento, la trazabilidad y el cumplimiento de las normas de calidad del proyecto.

## Refactorización de tests de modelos (enero 2026)

Se han unificado todos los tests de la capa models en el archivo `test_models.py`, eliminando los archivos fragmentados `test_opensearh_db.py` y `test_ttrss_postgre_db.py`. Todos los tests de modelos ahora están centralizados, con mocks para dependencias externas y generación de artefactos solo en la carpeta `tests/`.
Esta mejora refuerza la mantenibilidad, la trazabilidad y el cumplimiento de las normas de calidad y estructura definidas en `AGENTS.md`.
# ⚙️ Cambios en los Workflows de GitHub Actions

Resumen de las mejoras y correcciones aplicadas a los workflows en `.github/workflows/`.

---

## 📝 Resumen de cambios (2026-01-16)

- Eliminación de contenido duplicado (dos bloques `name: CI` y jobs repetidos)
- Corrección del trigger de `pull_request` para apuntar explícitamente a `main` y `master`
- Unificación del workflow en un único documento `ci.yml` con dos jobs: `security` y `tests`
- `security` ejecuta `pip_audit` y `bandit`, genera y sube artefactos JSON
- `tests` depende de `security`, usa un `matrix` con `python-version: [3.11, 3.12]` y ejecuta `pytest -q`

---

## 🔄 Unificación de Workflows (2026-01-19)

**Objetivo:** Unificar los workflows dispersos en un único pipeline de CI llamado `unified-ci.yml` en `.github/workflows/`.

**Estructura:**

| Stage              | Descripción                                                                 |
|:-------------------|:--------------------------------------------------------------------------|
| `setup`            | Preparación del entorno e instalación de dependencias                      |
| `lint`             | Análisis estático (`flake8`, `bandit`) y subida de reportes                |
| `security`         | Ejecución de `pip-audit` y subida del resultado                           |
| `unit-tests`       | Tests unitarios (matrix Python 3.11/3.12) y subida de logs                |
| `integration-tests`| Tests de integración dependientes de los unitarios                        |
| `coverage`         | Ejecución de cobertura de tests con `pytest-cov` y subida de reportes     |
| `cleanup`          | Stage final que siempre se ejecuta (`if: always()`), limpia caches y artefactos temporales |


**Visualización de cobertura en la UI:**

**Nota:** La sección de cobertura ha sido eliminada de la interfaz web. El informe HTML generado por `pytest-cov` solo está disponible como archivo estático en `htmlcov/` tras ejecutar los tests.

**Artifacts y telemetría:**
- `bandit_report.json` y `pip_audit.json` se suben como artifacts para su revisión
- Los logs de tests también se suben
- Los reportes de cobertura (`htmlcov/`, `coverage.xml`, `.coverage`) se suben como artifacts

**Acciones realizadas:**

- Añadido `.github/workflows/unified-ci.yml`
- Añadido job `coverage` para medir y reportar cobertura de tests (falla si baja del 80%)
- Eliminados los workflows individuales (si no se requiere mantenerlos en paralelo)

---

## Visualización de documentación en la UI

A partir de la versión [fecha actual], la interfaz de usuario incluye un apartado específico para la visualización de la documentación del proyecto. Esta funcionalidad permite consultar tanto el contenido de `README.md` como todos los archivos Markdown ubicados en la carpeta `Docs/` directamente desde la UI web.

### Características
- Acceso desde la barra lateral mediante el botón **Documentación**.
- Visualización en formato enriquecido (Markdown renderizado).
- Listado automático de todos los archivos `.md` de la carpeta `Docs/`.
- Selección y cambio dinámico de documento sin recargar la página.

### Implementación técnica
- Se ha añadido un endpoint REST (`/docs/list`, `/docs/readme`, `/docs/file/{filename}`) para exponer los archivos de documentación.
- La UI consume estos endpoints y renderiza el contenido usando un parser Markdown.
- El código fuente de la integración se encuentra en:
  - Backend: `src/app/controllers/routes/docs_controller.py`
  - Frontend: `src/app/ui/static/index.html`, `ui.js`, `styles.css`

### Requisitos
- El usuario debe tener acceso a la UI web.
- Los archivos de documentación deben estar presentes en el sistema de archivos del servidor.

### 2026-03-15: Lógica condicional LLM en code scanning

- El workflow de tests y CI verifica ahora que el análisis de código solo contacta con el LLM si el flag `use_ollama` está activado en algún `.ini` de `src/`. Si está en `false` en ambos, la explicación LLM se sustituye por el texto fijo "LLM desactivado por configuración.".
- Añadidos tests unitarios en `tests/unit/test_scanner_llm_flag.py` para cubrir este comportamiento.

