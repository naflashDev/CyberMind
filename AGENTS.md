## 🧪 Generación y ejecución de tests automatizados

La suite de tests debe generarse y ejecutarse siguiendo la Pirámide de Testing y las siguientes directrices:

- **Generación de tests:**
  - Los tests unitarios se ubican en `tests/unit/`, los de integración en `tests/integration/` y los E2E en `tests/e2e/`.
  - Cada test debe incluir comentarios indicando el caso cubierto (Happy Path, Edge Case, Error Handling).
  - Se debe cubrir el 100% de las funciones y al menos el 80% de las líneas de código.
  - Utiliza `pytest` para backend y `playwright` para E2E.

- **Ejecución de la suite:**
  - Para ejecutar todos los tests y medir cobertura:
    ```bash
    pytest --cov=src --cov-report=html
    ```
  - Para ejecutar solo los tests unitarios o de integración:
    ```bash
    pytest tests/unit
    pytest tests/integration
    ```
  - Para los tests E2E (Playwright):
    ```bash
    pytest tests/e2e
    # o bien
    playwright test tests/e2e
    ```
  - El reporte de cobertura HTML se genera en `htmlcov/index.html`.

Consulta el archivo `tests/README.md` para detalles y ejemplos.
# Agents.md

## 📌 Objetivo

Este documento define las **normas obligatorias de actuación del agente de IA (GitHub Copilot)** dentro del proyecto, así como los **estándares de desarrollo, documentación, pruebas, seguridad y automatización** que deben cumplirse en todo momento.

El incumplimiento de cualquiera de estas normas invalida el cambio realizado.

---

## 📝 Normas de codificación y comentarios

- **Cabecera de archivo obligatoria:**
  - Todo archivo Python (*.py*) que no sea `__init__.py` **DEBE** incluir al inicio una cabecera con el siguiente formato (adaptando los campos según corresponda):
    """
    @file NOMBRE_DEL_ARCHIVO.py
    @author naflashDev
    @brief [Breve descripción funcional del archivo.]
    @details [Descripción técnica o funcional ampliada.]
    """

- **Funciones nuevas:**
  - Toda función nueva **DEBE** incluir un docstring en la cabecera con la siguiente estructura (en inglés):
    '''
    @brief [Breve descripción de la función.]

    [Explicación técnica o funcional ampliada.]

    @param [nombre] [Descripción del parámetro.]
    ...
    @return [Descripción del valor de retorno.]
    '''
  - El nombre de las funciones **DEBE** seguir el formato *snake_case*.
  - Todo fragmento relevante de código dentro de la función **DEBE** estar comentado con comentarios *inline* que expliquen qué hace cada parte.
  - **Todos los comentarios de código deben estar redactados en inglés** (tanto cabecera como inline).

---

---

## 🤖 Agente de Inteligencia Artificial

- **Agente:** GitHub Copilot
- **Tipo:** Asistente de desarrollo
- **Ámbito de actuación:**
  - Generación y modificación de código
  - Propuestas de arquitectura
  - Generación y actualización de documentación
  - Creación de pruebas
  - Definición de workflows CI/CD

### Principio rector
> Ningún cambio es válido si no está **documentado, probado y automatizado**.

---

## 🧱 Descripción del proyecto

- **Tipo:** API REST
- **Dominio:** Servicios de Ciberseguridad
- **Características principales:**
  - Servicios de análisis, monitorización y protección
  - Integración de un módulo de Inteligencia Artificial
  - Arquitectura orientada a seguridad (*Security by Design*)
  - Preparado para integración y despliegue continuo (CI/CD)

---

## 🌍 Idioma de la documentación

- **Idioma obligatorio:** Español
- No se permite documentación en otros idiomas
- Los nombres de archivos pueden estar en inglés técnico, pero el contenido **DEBE** estar redactado en español claro y técnico

---

## 📂 Normas de documentación

### Carpeta obligatoria

```
/Docs
```

Todo cambio funcional, técnico o estructural **DEBE** documentarse mediante archivos Markdown (`.md`) dentro de esta carpeta.

### Reglas generales de documentación

- Antes de crear un nuevo documento, el agente **DEBE revisar los documentos existentes**
- Si la nueva información **encaja en un documento ya existente**, este **DEBE actualizarse**
- Solo se crearán nuevos documentos cuando no exista uno adecuado
- La documentación debe actualizarse **en el mismo commit** que el cambio de código
- No se permite código sin documentación asociada

---

## 🔗 Documentación de Endpoints de la API

### Archivo obligatorio

```
/Docs/api_endpoints.md
```

### Reglas específicas para endpoints

- Todo **nuevo endpoint**, modificación o eliminación **DEBE** documentarse en `api_endpoints.md`
- No se crearán archivos adicionales para endpoints salvo justificación técnica
- Cada endpoint debe documentarse incluyendo, como mínimo:
  - Método HTTP
  - Ruta
  - Descripción funcional
  - Parámetros de entrada
  - Respuestas posibles
  - Códigos de estado HTTP
  - Requisitos de autenticación y autorización

- Antes de añadir un endpoint:
  - Revisar si existe una sección relacionada
  - Agrupar endpoints por dominio o servicio cuando aplique

---

## 📝 Registro de cambios (ChangeLog)

### Archivo obligatorio

```
/Docs/ChangeLog.md
```

### Estándar requerido

El ChangeLog **DEBE** seguir estrictamente el formato definido en:

👉 https://keepachangelog.com/es-ES/1.0.0/

### Categorías permitidas
- `Added`
- `Changed`
- `Deprecated`
- `Removed`
- `Fixed`
- `Security`

### Reglas
- Todo cambio debe quedar registrado
- Cada versión debe incluir fecha
- Los cambios de seguridad **DEBEN** ir en `Security`
- No se aceptan commits sin actualización del ChangeLog

---

## 🧪 Pruebas obligatorias

Cada cambio en el código **DEBE** incluir pruebas automatizadas.

### Tipos de pruebas requeridas

#### 1. Tests unitarios
- Validación de funciones, clases y módulos
- Cobertura de casos normales y extremos

#### 2. Tests de integración
- Interacción entre servicios
- Validación de endpoints
- Integración con IA, bases de datos y servicios externos

#### 3. Tests de seguridad (cuando aplique)
- Validación de entradas
- Prevención de inyecciones
- Comprobación de autenticación y autorización

### Normas
- Ningún cambio puede reducir la cobertura de tests
- Los tests deben ejecutarse automáticamente en CI
- El código sin tests se considera inválido

---

## ⚙️ Automatización y CI/CD

### Workflows obligatorios

Todos los workflows deben ubicarse en:

```
.github/workflows/
```

### Workflows mínimos requeridos

#### ✅ Integración continua (CI)
- Instalación de dependencias
- Ejecución de tests unitarios
- Ejecución de tests de integración

#### 🔐 Seguridad
- Análisis estático de código (SAST)
- Auditoría de dependencias
- Comprobación de vulnerabilidades conocidas

#### 🚀 Despliegue continuo (CD) *(si aplica)*
- Build del proyecto
- Despliegue automatizado
- Validaciones post-despliegue

### Reglas
- Ningún merge sin CI en verde
- Todo workflow debe estar documentado en `/Docs`
- Los fallos de seguridad bloquean el pipeline

---

## 🔒 Seguridad

La seguridad es prioritaria en todo el ciclo de vida del proyecto.

### Reglas de seguridad
- Validación estricta de entradas
- Manejo seguro de secretos
- Principio de mínimo privilegio
- Evitar dependencias inseguras

### Cambios de seguridad
- Deben documentarse explícitamente
- Deben incluir pruebas específicas
- Deben registrarse en `ChangeLog.md` → `Security`

---

## 🧠 Inteligencia Artificial

Los componentes de IA están sujetos a normas adicionales.

### Documentación obligatoria

```
/Docs/IA.md
```

Debe incluir:
- Modelo o enfoque utilizado
- Datos de entrada y salida
- Riesgos de seguridad y mitigaciones
- Limitaciones conocidas

### Pruebas de IA
- Validación de comportamiento esperado
- Manejo de entradas maliciosas
- Control de errores y fallos del modelo

---

## 🚫 Restricciones del agente de IA

GitHub Copilot **NO DEBE**:
- Introducir código sin tests
- Modificar código sin documentación
- Crear documentos duplicados innecesarios
- Omitir el ChangeLog
- Ignorar requisitos de seguridad
- Realizar cambios no trazables

---

## ✅ Cumplimiento y autoridad

Este archivo es la **fuente de verdad** para el comportamiento del agente de IA y el desarrollo del proyecto.

Cualquier cambio que no cumpla estas normas:
- Debe ser rechazado
- Debe corregirse antes de ser aceptado

---

## 📎 Notas finales

- Este documento debe revisarse periódicamente
- Cualquier modificación del propio `Agents.md` también debe:
  - Documentarse
  - Registrarse en el ChangeLog
