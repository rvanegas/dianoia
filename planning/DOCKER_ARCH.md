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
- **Config:** `~/dianoia/.env` on the box (`ANTHROPIC_API_KEY`, `NOESIS_TOKEN`,
  `NOESIS_URL`, `NOESIS_CLIENT_IDS`, `CORS_ORIGINS`; CLAUDE.md
  says what each is), never in the repo and never sent by a deploy.
- **Health:** `GET /healthz` returns `{"ok": true, "commit": …}`, the commit
  stamped into `src/deployed.json` by `ts deploy`.

## Deploying

From the Mac:

```bash
ts deploy
```

technosophia's shared deploy, with dianoia's settings in `bin/ts.env` and its
own steps in `bin/hooks/`: the whole test suite first (`deploy-pre`), then an rsync of the checkout to `~/dianoia` on commons
(the `commons` ssh alias), `docker compose up --build -d` (`deploy-remote`),
and a wait for `/healthz` to report the commit it sent, on the box and at
`https://dianoia.rvanegas.co`. Each deploy is recorded on the box; `ts deploys`
reads them.

The box itself is provisioned by `~/src/rvanegas-site/bin/provision-commons`.

## External clients

Roxana (in the browser) and noesis call `https://dianoia.rvanegas.co/api/`.
`https://dianoia.rvanegas.com` still serves noesis with dianoia under `/api/`,
for anything holding the old name.
