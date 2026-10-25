# Docker Architecture

## Overview

Dianoia runs as one container on the shared **commons** box (Lightsail,
planned in `~/src/rvanegas-site/SITE.md`). The box's Caddy is the only thing
listening publicly; it terminates TLS and proxies to dianoia on loopback.

```
Internet
   │
   ▼
[Caddy]  ports 80/443, certificates renewed by Caddy itself
   │  dianoia.rvanegas.co        → 127.0.0.1:8000 (everything)
   │  noesis.rvanegas.co /api/*  → 127.0.0.1:8000
   │  dianoia.rvanegas.com       → as noesis (the old name)
   ▼
[dianoia-backend-1]  uvicorn, published on 127.0.0.1:8000 only
```

Noesis is no longer a container: Caddy serves its built `dist/` from
`/srv/noesis`. The Caddyfile is `~/src/rvanegas-site/Caddyfile`; ports for
every service on the box are in `~/src/rvanegas-site/PROJECTS.md`.

## The container

- **Image:** built from `Dockerfile` (Python 3.13, uvicorn), on the box.
- **Published:** `127.0.0.1:8000` — reachable by Caddy, never from outside.
- **Config:** `~/dianoia/.env` on the box (`ANTHROPIC_API_KEY`, `MDC_TOKEN`),
  never in the repo and never sent by a deploy.
- **Health:** `GET /healthz` returns `{"ok": true, "commit": …}`, the commit
  stamped into `src/deployed.json` by `bin/deploy`.

## Deploying

From the Mac:

```bash
bin/deploy
```

It rsyncs the checkout to `~/dianoia` on commons (32.190.173.222;
`COMMONS_HOST` overrides), runs `docker compose up --build -d`, and waits for
`/healthz` to report the commit it sent, on the box and at
`https://dianoia.rvanegas.co`. See the script's header.

The box itself is provisioned by `~/src/rvanegas-site/bin/provision-commons`.

## External clients

Roxana (in the browser) and mdc call `https://dianoia.rvanegas.co/api/`.
`https://dianoia.rvanegas.com` still serves noesis with dianoia under `/api/`,
for anything holding the old name.
