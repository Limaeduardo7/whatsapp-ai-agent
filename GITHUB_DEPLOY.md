# GitHub e Deploy

Repositorio: https://github.com/Limaeduardo7/whatsapp-ai-agent

## Publicacao

Use git/gh autenticado localmente:

```bash
git status
git add .
git commit -m "describe change"
git push -u origin branch-name
```

Evite salvar tokens GitHub em arquivos como `~/.git-credentials`.

## CI

O workflow em `.github/workflows/ci.yml` executa:

- instalacao do pacote com dependencias de desenvolvimento,
- `ruff check src tests`,
- `pytest`.

## Deploy local com systemd

```bash
sudo ./scripts/deploy.sh
```

O script cria o usuario de sistema `whatsapp-agent`, instala dependencias e registra `config/evolution-bridge.service`.

## Deploy com Docker

```bash
docker compose up --build
```
