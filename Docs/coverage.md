# Test de coverage para CyberMind

## Estado actual (2026-01-25)

- La cobertura de `src/app/controllers/routes/llm_controller.py` supera el 80% tras la ampliación de tests para ramas de error y condiciones límite.
- Se han añadido pruebas para excepciones en eventos y timers, cumpliendo la política de calidad definida en `AGENTS.md`.


Este script ejecuta los tests del proyecto y genera un informe de cobertura utilizando pytest-cov.

## Uso


Desde la raíz del proyecto, ejecuta:

```
 /CyberMind/env/Scripts/python.exe -m pytest --cov=src --cov-report=term-missing --cov-report=html
```

- El informe HTML se genera en `htmlcov/`.
- El test fallará si la cobertura baja del 80%.

## Integración en CI

Añade el siguiente paso al workflow de CI para validar la cobertura:

```
- name: Ejecutar tests y coverage
  run: |
    pip install -r dev-requirements.txt
    pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=80
```

## Referencias
- [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/)
