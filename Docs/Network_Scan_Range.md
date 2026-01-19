 # Network Scan Range

Documento que explica el endpoint `POST /network/scan_range` y su uso desde la UI.

## Descripción

- Escanea un bloque CIDR o un rango `start`/`end` y devuelve, por host, la lista de puertos analizados con estados y metadatos.

## Payload (JSON)

- `cidr` (string, opcional): bloque CIDR (ej. `192.168.1.0/28`). Si se especifica, se ignoran `start`/`end`.
- `start` (string, opcional): IP de inicio del rango.
- `end` (string, opcional): IP final del rango. Si no está, se escanea solo `start`.
- `ports` (array|string, opcional): lista de puertos o CSV (`"22,80"`). Si se omite, se usan puertos comunes.
- `timeout` (number, opcional): timeout por host (segundos). Valor por defecto en la API.
- `use_nmap` (bool, opcional): intenta ejecutar `nmap` si está `true`, si no hay `nmap` usa fallback TCP.
- `concurrency` (int, opcional): controla concurrencia; la API aplica límites por seguridad.

## Respuesta

JSON con listado de hosts, resultados por puerto y tiempos. Cada `result` incluye `port`, `open` (bool), `state` (string: `open|closed|filtered|unknown`) y `service`.

Ejemplo simplificado:

```json
{
  "scanned": 2,
  "hosts": [
    {
      "host": "192.168.1.1",
      "results": [
        {"port":22,"open":true,"state":"open","service":"ssh"}
      ],
      "duration_seconds": 0.45
    }
  ],
  "duration_seconds": 1.23
}
```

## Restricciones y seguridad

- Máximo 1024 hosts por petición. Peticiones con más hosts devuelven `400`.
- Registrar y monitorear peticiones de escaneo (audit log).
- Nota legal: sólo realizar escaneos contra hosts bajo control o con autorización explícita.

## Errores comunes

- `400` — Payload inválido o número de hosts superior al límite.
- `500` — Error interno; revisar logs del servicio `network_analysis`.

## Referencias internas

- Código: `src/app/services/network_analysis/network_analysis.py` (función `scan_range`).
- Ruta: `src/app/controllers/routes/network_analysis_controller.py`.
