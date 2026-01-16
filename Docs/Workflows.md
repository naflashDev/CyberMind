# Cambios en los Workflows de GitHub Actions

Descripción breve de las correcciones aplicadas a los workflows en `.github/workflows/`.

## Resumen de cambios (2026-01-16)

- Archivo modificado: `.github/workflows/ci.yml`.
- Problemas detectados:
  - Contenido duplicado en el archivo (dos bloques `name: CI` y jobs repetidos), lo que causaba configuración confusa y posibles errores en la ejecución.
  - Trigger de `pull_request` con `branches: [ '*' ]`, que no es una práctica recomendada y puede comportarse de forma inesperada.

- Soluciones aplicadas:
  - Unificación del workflow en un único documento `ci.yml` con dos jobs: `security` y `tests`.
  - Corrección de `pull_request` para que apunte explícitamente a `main` y `master`.
  - `security` ejecuta `pip_audit` y `bandit`, genera `pip_audit.json` y `bandit_report.json` y sube ambos como artifacts.
  - `tests` depende de `security`, usa un `matrix` con `python-version: [3.11, 3.12]` y ejecuta `pytest -q`.

## Notas y siguientes pasos

- Documentación: entrada agregada en `Docs/ChangeLog.md`.
- Revisión recomendada: verificar en la siguiente ejecución de CI que los artifacts se suben correctamente.
- Si quieres, puedo:
  - Ejecutar `pytest` localmente en el entorno virtual del repositorio y reportar fallos.
  - Añadir cache para dependencias en el job `tests` si así lo prefieres.

Si confirmas, procedo con pruebas locales o ajustes adicionales.
