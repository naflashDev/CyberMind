# Guía de Containerización y Despliegue de CyberMind

Esta guía describe el despliegue y administración de CyberMind mediante **Docker Compose**, con arquitectura de servicios desacoplada, asignación controlada de recursos y conexión con la inferencia de Ollama en la máquina anfitriona.

---

## 🏗️ Servicios Desplegados

1. **`cybermind-frontend` (`:8080`)**:
   - Single Page Application construida con React, TypeScript, Tailwind CSS, Lucide Icons y empaquetada en un contenedor Nginx Alpine ultra-ligero.
   - Cuenta con selector de 6 paletas cromáticas (Guía de naflashDev) y Modo Oscuro nativo.
2. **`cybermind-backend` (`:8000`)**:
   - API REST en FastAPI que orquesta tareas NLP, spiders asíncronos y análisis SAST.
   - Incluye `nmap` nativo instalado en el contenedor.
   - Conectado a la base de datos vectorial **ChromaDB** persistente en `./data/chroma`.
3. **`cybermind-postgres` (`:5432`)**:
   - Base de datos relacional PostgreSQL 15 Alpine para Tiny Tiny RSS y spiders dinámicos.
4. **`cybermind-opensearch` & `dashboards` (`:9200` y `:5601`)**:
   - Almacenamiento y panel analítico de noticias e indicadores de compromiso.
5. **`cybermind-ttrss` (`:8280`)**:
   - Agregador de noticias y feeds RSS de ciberseguridad.
6. **Inferencia Ollama (Host)**:
   - El backend se comunica con la instancia de Ollama instalada nativamente en el host vía `http://host.docker.internal:11434`.

---

## ⚡ Comandos Rápidos de Despliegue

### 1. Iniciar toda la suite
```bash
docker compose up -d --build
```

### 2. Verificar estado de los contenedores
```bash
docker compose ps
```

### 3. Ver logs en tiempo real
```bash
# Ver todos los logs
docker compose logs -f

# Ver únicamente los logs del backend
docker compose logs -f backend
```

### 4. Detener los servicios
```bash
docker compose down
```

---

## 🛡️ Límites de Recursos Asignados

| Servicio | Límite CPU | Límite RAM | Reserva RAM |
| :--- | :--- | :--- | :--- |
| **Frontend** | 0.5 CPU | 128 MB | 32 MB |
| **Backend** | 1.5 CPU | 1024 MB | 256 MB |
| **PostgreSQL** | 1.0 CPU | 512 MB | 128 MB |
| **OpenSearch** | 2.0 CPU | 1536 MB | 512 MB |
| **Dashboards** | 1.0 CPU | 512 MB | 256 MB |
| **Tiny RSS** | 0.5 CPU | 256 MB | 64 MB |
