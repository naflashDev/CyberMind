

# 📰 Instalación y configuración de TinyRSS para CyberMind (Docker Compose)

Guía para instalar y configurar **TinyRSS** como servicio auxiliar de **CyberMind** usando Docker Compose (recomendado en WSL).

---

## 1️⃣ Requisitos previos

- **WSL2** instalado y funcionando
- **Docker Desktop** con soporte para WSL2
- **Docker Compose** instalado
- Terminal dentro de la distribución Linux de WSL (ej. Ubuntu)

> 📁 Todos los archivos necesarios (`stack.env`, `tinytinyrss.yml`) están en la carpeta `Install/`.

---

## 2️⃣ Archivo de entorno (`stack.env`)

Ejemplo de contenido de `stack.env`:

```env
TTRSS_DB_USER=postgres
TTRSS_DB_NAME=postgres
TTRSS_DB_PASS=password123
HTTP_PORT=127.0.0.1:8280
```

- `TTRSS_DB_USER`, `TTRSS_DB_NAME`, `TTRSS_DB_PASS`: credenciales de la base de datos PostgreSQL para TinyRSS
- `HTTP_PORT`: puerto local donde se expondrá TinyRSS

> ⚠️ **Importante:** El fichero `stack.env` debe existir en la misma carpeta que `tinytinyrss.yml` (`Install/`). El compose usa estas variables para configurar la base de datos y el puerto. Si falta, la ejecución fallará.

Puedes crear una copia y personalizarla:

```bash
cp Install/stack.env.example Install/stack.env  # si hay template
# o crear manualmente
cat > Install/stack.env <<'EOF'
TTRSS_DB_USER=postgres
TTRSS_DB_NAME=postgres
TTRSS_DB_PASS=password123
HTTP_PORT=127.0.0.1:8280
EOF
```

---

## 3️⃣ Docker Compose para TinyRSS (`tinytinyrss.yml`)

Ejemplo de contenido de `tinytinyrss.yml`:

```yaml
version: '3'

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    env_file:
      - stack.env
    environment:
      - POSTGRES_USER=${TTRSS_DB_USER}
      - POSTGRES_PASSWORD=${TTRSS_DB_PASS}
      - POSTGRES_DB=${TTRSS_DB_NAME}
    volumes:
      - db:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  app:
    image: cthulhoo/ttrss-fpm-pgsql-static:latest
    restart: unless-stopped
    env_file:
      - stack.env
    volumes:
      - app:/var/www/html
      - ./config.d:/opt/tt-rss/config.d:ro
    depends_on:
      - db

  updater:
    image: cthulhoo/ttrss-fpm-pgsql-static:latest
    restart: unless-stopped
    env_file:
      - stack.env
    volumes:
      - app:/var/www/html
      - ./config.d:/opt/tt-rss/config.d:ro
    depends_on:
      - app
    command: /opt/tt-rss/updater.sh

  web-nginx:
    image: cthulhoo/ttrss-web-nginx:latest
    restart: unless-stopped
    env_file:
      - stack.env
    ports:
      - ${HTTP_PORT}:80
    volumes:
      - app:/var/www/html:ro
    depends_on:
      - app

volumes:
  db:
  app:
  backups:
```

---

## 4. Crear los volúmenes de Docker

Si no existen, crea los volúmenes necesarios:

```bash
docker volume create db
docker volume create app
docker volume create backups
```

---

- ## 5. Iniciar TinyRSS con Docker Compose

Antes de levantar los contenedores, asegúrate de que `Install/stack.env` existe y contiene las variables necesarias (ver sección anterior).

Ejemplos de comandos según la versión de Docker Compose que uses:

- Docker Compose v2 (incluido en Docker Desktop / `docker compose`):

```bash
cd Install
docker compose --env-file stack.env -f tinytinyrss.yml up -d
```

- Docker Compose v1 (binario `docker-compose`):

```bash
cd Install
docker-compose --env-file stack.env -f tinytinyrss.yml up -d
```

- `-d`: ejecuta los contenedores en segundo plano.
- Servicios que se levantarán:
  - `db`: PostgreSQL
  - `app`: TinyRSS PHP-FPM
  - `updater`: script de actualización
  - `web-nginx`: servidor web Nginx
  - `nginx-proxy-manager`: proxy inverso opcional

---

## 6. Acceder a TinyRSS

1. Abre un navegador y visita:

```
http://127.0.0.1:8280
```

2. Credenciales del administrador:

```
Usuario: admin
Contraseña: Mirar en el docker desktop
```

Docker Descktop --> Containers --> install --> install_app_1 (hacemos click y aparece un mensaje como este)
```
*****************************************************************************

* Setting initial built-in admin user password to 'eoKpCfHmfOVYHwsN'        *

* If you want to set it manually, use ADMIN_USER_PASS environment variable. *

*****************************************************************************
```


---

## 7. Administrar los contenedores

- **Ver logs:**

```bash
docker-compose -f tinytinyrss.yml logs -f
```

- **Detener todos los contenedores:**

```bash
docker-compose -f tinytinyrss.yml down
```

- **Reiniciar los contenedores:**

```bash
docker-compose -f tinytinyrss.yml up -d
```

---


