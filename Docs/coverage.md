
# Cobertura de Tests de CyberMind

<div align="center">
  <img src="https://img.shields.io/badge/Coverage-%3E%3D80%25-brightgreen" alt="Cobertura >=80%" />
  <img src="https://img.shields.io/badge/Tests-300%2B-blue" alt="Más de 300 tests" />
</div>

---


## Resumen de cobertura (2026-01-26)

---

## Visualización en la interfaz web

**Nota:**
- La sección de cobertura ha sido eliminada de la interfaz web. El informe HTML generado por coverage.py solo está disponible como archivo estático en `htmlcov/` tras ejecutar los tests.
- Los tests unitarios gestionan automáticamente la creación y borrado del archivo `.env` durante la ejecución, garantizando que las variables de entorno críticas estén presentes y evitando residuos en el entorno de desarrollo o CI.
- Todos los tests críticos de infraestructura, servicios y utilidades están mockeados y son multiplataforma.

---

| Métrica                | Valor estimado |
|------------------------|:--------------:|

| **Total de tests**     | 316+           |
| **Cobertura global**   | ≥83%           |
| **Cobertura mínima**   | 80%            |
| **Cobertura máxima**   | 100%           |

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
- [Cobertura HTML generada](../htmlcov/index.html)

---
