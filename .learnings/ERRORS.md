# ERRORS

## [ERR-20260309-001] veo3-video-gen

**Logged**: 2026-03-09T21:22:59Z
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
Falha ao gerar primeiro vídeo com referência de imagem por quota esgotada na Gemini API (Veo).

### Error
```
429 RESOURCE_EXHAUSTED: You exceeded your current quota, please check your plan and billing details.
```

### Context
- Comando: generate_video.py com model veo-3.1-generate-preview
- Entrada: imagem do personagem enviada pelo usuário
- Ambiente: venv local em /root/clawd/.venv-video

### Suggested Fix
Ativar billing/quota para Gemini API vídeo (Veo) ou usar outra credencial com cota disponível.

### Metadata
- Reproducible: yes
- Related Files: skills/veo3-video-gen/scripts/generate_video.py

---
