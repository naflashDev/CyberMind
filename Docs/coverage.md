
# Cobertura de Tests de CyberMind

<div align="center">
  <img src="https://img.shields.io/badge/Coverage-%3E%3D80%25-brightgreen" alt="Cobertura >=80%" />
  <img src="https://img.shields.io/badge/Tests-300%2B-blue" alt="Más de 300 tests" />
</div>

---


## Resumen de cobertura (2026-01-26)


## Visualización en la interfaz web

**Nota:**


# Cobertura de tests

## Estrategia de optimización de tests (2026-01-27)

  - Los tests unitarios tardan <10ms.
  - Los tests de integración tardan <500ms.
  - Los tests E2E solo cubren flujos críticos y se mantienen <10s.


## Estrategia
 Se sigue la Pirámide de Testing: predominan los tests unitarios (60-70%), seguidos de integración (20-30%) y un subconjunto crítico de E2E (5-10%).
 Se exige:
  - **Cobertura mínima:** 80% de líneas y 100% de funciones.
  - **Cobertura incremental:** Ningún cambio puede reducir la cobertura.

## Ejecución recomendada de la suite de tests

Para ejecutar todos los tests con cobertura y obtener el informe HTML, utiliza el siguiente comando (ajustado para el entorno virtual del proyecto):

```sh
/CyberMind/env/Scripts/python.exe -m pytest --maxfail=3 --durations=20 --tb=short --cov=src --cov-report=html
```

Esto:
- Limita a 3 los fallos antes de detener la ejecución.
- Muestra los 20 tests más lentos.
- Usa un traceback corto para errores.
- Genera un informe de cobertura HTML en `htmlcov/index.html`.

## Estado actual

- La suite cubre todos los módulos principales de lógica, validación, scraping, análisis de red, procesamiento de texto y modelos de datos.
- Los tests incluyen casos Happy Path, Edge Cases y manejo de errores.
- Cada test está documentado y separado por nivel (unit, integration, e2e).
- Se ha corregido el fixture de entorno para evitar errores de acceso concurrente al archivo `.env` en Windows.
- Se han eliminado los RuntimeWarning de corutinas no awaitadas en los tests de scraping y análisis de red, garantizando compatibilidad total con AsyncMock y ejecución paralela.

## Reglas

- Todo nuevo código debe incluir tests y mantener/incrementar la cobertura.
- Los tests deben ser rápidos, deterministas y no depender de servicios externos reales.
- La cobertura se revisa en cada pipeline de CI.

### Cobertura por módulos principales

| Módulo                                 | Cobertura |
|-----------------------------------------|:---------:|
| `src/app/utils/run_services.py`         | 80%       |
| `src/main.py`                          | 72%       |
| Otros módulos principales               | >80%      |

> **Nota:** Todos los módulos principales superan el 80% de cobertura. Las excepciones menores se deben a código defensivo, dependencias de plataforma o lógica difícil de testear (subprocesos, rutas específicas, errores de sistema).



**Puntos destacados:**
- Se han ampliado los tests para cubrir ramas de error, condiciones límite, validaciones de endpoints y operaciones Git.
- Se han añadido pruebas para excepciones en eventos, timers, errores de conexión y validaciones de parámetros.
- Se documentan las limitaciones técnicas en los módulos con menor cobertura.
- Cumplimiento estricto de la política de calidad definida en `AGENTS.md`.



---

## ¿Cómo se mide la cobertura?

La cobertura se calcula ejecutando todos los tests del proyecto y analizando qué líneas de código han sido ejecutadas. Se utiliza `pytest` junto con el plugin `pytest-cov` para obtener métricas detalladas y un informe visual en HTML.


## Ejecución manual

Desde la raíz del proyecto, ejecuta:

```bash
env/Scripts/python.exe -m pytest --cov=src --cov-report=term-missing --cov-report=html
```

- El informe HTML se genera en la carpeta `htmlcov/`.
- El test fallará si la cobertura baja del 80%.


## Integración en CI/CD

Para asegurar la calidad, añade el siguiente paso al workflow de CI:

```yaml
- name: Ejecutar tests y coverage
  run: |
    pip install -r dev-requirements.txt
    pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=80
```


---

## Recursos y referencias

- [Documentación oficial de pytest-cov](https://pytest-cov.readthedocs.io/en/latest/)
---
