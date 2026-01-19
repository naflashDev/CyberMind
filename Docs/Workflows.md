# Cambios en los Workflows de GitHub Actions

Descripción breve de las correcciones aplicadas a los workflows en `.github/workflows/`.

## Resumen de cambios (2026-01-16)

  - Contenido duplicado en el archivo (dos bloques `name: CI` y jobs repetidos), lo que causaba configuración confusa y posibles errores en la ejecución.
  - Trigger de `pull_request` con `branches: [ '*' ]`, que no es una práctica recomendada y puede comportarse de forma inesperada.

  - Unificación del workflow en un único documento `ci.yml` con dos jobs: `security` y `tests`.
  - Corrección de `pull_request` para que apunte explícitamente a `main` y `master`.
  - `security` ejecuta `pip_audit` y `bandit`, genera `pip_audit.json` y `bandit_report.json` y sube ambos como artifacts.
  - `tests` depende de `security`, usa un `matrix` con `python-version: [3.11, 3.12]` y ejecuta `pytest -q`.

## Unificación de Workflows (2026-01-19)

- **Objetivo:** Unificar los workflows dispersos en un único pipeline de CI llamado `unified-ci.yml` ubicado en `.github/workflows/`.
- **Estructura:** El workflow está organizado en stages claramente identificadas (jobs con `needs` que representan el flujo):
  - `setup`: preparación del entorno e instalación de dependencias.
  - `lint`: análisis estático (`flake8`, `bandit`) y subida de reportes como artifacts.
  - `security`: ejecución de `pip-audit` y subida del resultado.
  - `unit-tests`: tests unitarios (matrix Python 3.11/3.12) y subida de logs.
  - `integration-tests`: tests de integración dependientes de los unitarios.
  - `cleanup`: stage final que siempre se ejecuta (`if: always()`), limpia caches y artefactos temporales.

- **Artifacts y telemetría:** `bandit_report.json` y `pip_audit.json` se suben como artifacts para su revisión; los logs de tests también se suben.
- **Acciones realizadas:** Se añadió `.github/workflows/unified-ci.yml` y se han eliminado los workflows individuales (siempre que no quieras mantenerlos en paralelo).

Si quieres que mantenga una copia de respaldo de los workflows anteriores en `/.github/workflows/backup/`, lo añado ahora.
## Notas y siguientes pasos

- Documentación: entrada agregada en `Docs/ChangeLog.md`.
- Revisión recomendada: verificar en la siguiente ejecución de CI que los artifacts se suben correctamente.
- Si quieres, puedo:
  - Ejecutar `pytest` localmente en el entorno virtual del repositorio y reportar fallos.
  - Añadir cache para dependencias en el job `tests` si así lo prefieres.

Si confirmas, procedo con pruebas locales o ajustes adicionales.
