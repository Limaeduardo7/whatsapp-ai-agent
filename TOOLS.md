# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## UI/UX & Frontend

**SEMPRE usar a skill UI/UX Pro Max** para trabalhos de frontend, landing pages e design de interfaces.

### Como usar:
```bash
# Gerar design system completo
python3 /root/clawd/skills/ui-ux-pro-max-skill/src/ui-ux-pro-max/scripts/search.py "<query>" --design-system -p "<NomeProjeto>"

# Buscar estilos específicos
python3 /root/clawd/skills/ui-ux-pro-max-skill/src/ui-ux-pro-max/scripts/search.py "glassmorphism" --domain style

# Buscar paletas de cores
python3 /root/clawd/skills/ui-ux-pro-max-skill/src/ui-ux-pro-max/scripts/search.py "spa wellness" --domain color

# Buscar tipografia
python3 /root/clawd/skills/ui-ux-pro-max-skill/src/ui-ux-pro-max/scripts/search.py "elegant serif" --domain typography
```

### Recursos disponíveis:
- 67 estilos de UI (Glassmorphism, Minimalism, Brutalism, etc.)
- 96 paletas de cores por indústria
- 57 combinações de fontes com Google Fonts
- 100 regras de raciocínio por indústria
- Checklists de pré-entrega (acessibilidade, responsividade)

---

Add whatever helps you do your job. This is your cheat sheet.
\n### Telegram\n- Use chat id 899831670 for Eduardo notifications (do not use @limaeduardo).
