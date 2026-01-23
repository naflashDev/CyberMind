
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

