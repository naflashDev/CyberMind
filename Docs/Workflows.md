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

| Stage | Descripción |
|:---|:---|
| `setup` | Preparación del entorno e instalación de dependencias |
| `lint` | Análisis estático (`flake8`, `bandit`) y subida de reportes |
| `security` | Ejecución de `pip-audit` y subida del resultado |
| `unit-tests` | Tests unitarios (matrix Python 3.11/3.12) y subida de logs |
| `integration-tests` | Tests de integración dependientes de los unitarios |
| `cleanup` | Stage final que siempre se ejecuta (`if: always()`), limpia caches y artefactos temporales |

**Artifacts y telemetría:**

- `bandit_report.json` y `pip_audit.json` se suben como artifacts para su revisión
- Los logs de tests también se suben

**Acciones realizadas:**

- Añadido `.github/workflows/unified-ci.yml`
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

---

