# Docker Architecture

## Overview

Dianoia (backend) and Noesis (frontend) are separate repos that deploy independently to the same server. A shared Docker network (`app-network`) lets the two containers communicate without exposing the backend to the public internet.

```
Internet
   │
   ▼
[noesis_frontend_1]  nginx, ports 80/443
   │  serves React app at /
   │  proxies /api/ → http://backend:8000
   │
   └── app-network ──▶ [dianoia_backend_1]  uvicorn, port 8000 (internal only)
```

## Containers

### dianoia (this repo)

- **Image:** built from `Dockerfile` (Python 3.13, uvicorn)
- **Exposed:** nothing — only reachable within `app-network`
- **Config:** environment variables loaded from `.env`

### noesis (`~/src/noesis`)

- **Image:** two-stage build — Node 22 builds the React app, nginx serves the `dist/`
- **Exposed:** ports 80 and 443 on the host
- **TLS:** nginx reads certs from `/etc/letsencrypt` (mounted read-only from the host)
- **API proxy:** nginx forwards `/api/` requests to `http://backend:8000` over `app-network`

## Shared network

`app-network` is an external Docker bridge network created once on the server:

```bash
docker network create app-network
```

Both `docker-compose.yml` files declare it as external, so each repo can be deployed independently without disrupting the other.

## Deploying

Deploy either service independently:

```bash
git pull && docker-compose up -d --build
```

First-time setup on a new server:

```bash
# 1. Create the shared network (once)
docker network create app-network

# 2. Deploy dianoia
cd ~/dianoia && git pull && docker-compose up -d --build

# 3. Deploy noesis
cd ~/noesis && git pull && docker-compose up -d --build
```

> **Note:** dianoia must be running before noesis starts, because nginx resolves the `backend` hostname at startup. If noesis starts first, restart it after dianoia is up: `docker-compose restart`

## External clients

Roxana (a separate frontend on a different server) calls the API via the public URL `https://dianoia.rvanegas.com/api/`. Its requests pass through noesis's nginx, which proxies them to the backend over `app-network` — the same path as noesis's own API calls.
