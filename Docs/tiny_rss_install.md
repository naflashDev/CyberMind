# Instalación y configuración de TinyRSS con Docker Compose en WSL

Este documento describe cómo instalar y configurar **TinyRSS** usando **Docker Compose** dentro de WSL, empleando los archivos `stack.env`, `tinytinyrss.yml` y `nginx-proxy-manager.yml`, que ya se encuentran creados en la carpeta `install`.

---

## 1. Requisitos previos

- **WSL2** instalado y funcionando.
- **Docker Desktop** con soporte para WSL2.
- **Docker Compose** instalado.
- Una terminal dentro de la distribución Linux de WSL (por ejemplo Ubuntu).

> Todos los archivos necesarios (`stack.env`, `tinytinyrss.yml`) se encuentran en la carpeta `install`.

---

## 2. Archivo de entorno (`stack.env`)

Contenido del archivo `stack.env`:

```env
TTRSS_DB_USER=postgres
TTRSS_DB_NAME=postgres
TTRSS_DB_PASS=password123
HTTP_PORT=127.0.0.1:8280
```

- `TTRSS_DB_USER`, `TTRSS_DB_NAME`, `TTRSS_DB_PASS`: credenciales de la base de datos PostgreSQL para TinyRSS.
- `HTTP_PORT`: puerto local donde se expondrá TinyRSS.

---

## 3. Docker Compose para TinyRSS (`tinytinyrss.yml`)

Contenido del archivo `tinytinyrss.yml`:

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

## 5. Iniciar TinyRSS con Docker Compose

Desde la carpeta `install`, ejecuta la instrucción unificada que levanta **TinyRSS y Nginx Proxy Manager**:

```bash
sudo docker-compose -f tinytinyrss.yml --env-file stack.env up -d
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


