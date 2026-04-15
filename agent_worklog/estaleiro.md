# Worklog: Estaleiro (Frontend)
## Tarefa Atual
- ID: t1772359226636
- Título: Fix performance Meraki: FCP/LCP/TBT crítico
- Status: in_progress

## Progresso
- [x] Migrar framer-motion para LazyMotion + `m` components (commit 09f4b0c)
- [x] vendor-motion bundle: 115KB → 73KB (-37%), gzip 38KB → 26KB (-32%)
- [x] Remove framer-motion + 3 parallax scroll listeners from HeroParallaxDemo (commit ca2b2e1)
- [x] 15 per-slide JS animations replaced with CSS transitions
- [x] IntersectionObserver for section entry (no scroll listener)
- [x] Remove ALL 8 useParallax hooks from Index.tsx — eliminated scroll listener entirely (commit 887a946)
- [x] Replace 6 continuously-animating m.div radial gradients with 2 static CSS gradients
- [x] Remove animated SVG background pattern (infinite loop)
- [x] **Remove ALL 53 framer-motion m.div/svg/img from Index.tsx** (commit b36c4c1)
  - Exit popup → CSS scale-in animation
  - Hero entrance → CSS fadeUp/fadeScale
  - 2 floating elements → CSS infinite keyframes
  - 3 avatar images → CSS staggered slide-in
  - SVG underline → CSS stroke-dashoffset draw
  - 17 whileInView blocks → useScrollAnimation (IntersectionObserver)
  - framer-motion now ONLY lazy-loaded via HeroParallaxDemo
  - Zero JS animation framework overhead on initial page load
- [x] Build de produção OK (Index.js: 46KB)

## Arquivos Modificados
- /root/clawd/meraki-glow-design/src/pages/Index.tsx — removed ALL framer-motion imports/usage, replaced with CSS animations + useScrollAnimation
- /root/clawd/meraki-glow-design/src/index.css — added CSS keyframes: heroFadeUp, heroFadeScale, popupScaleIn, floatUp, floatDown, avatarSlideIn, svgDraw

## Bloqueios
- **Git push falha por autenticação** (token inválido) — precisa de novo token GitHub. Commits acumulados: 09f4b0c, ca2b2e1, 887a946, b36c4c1

## Próximos Passos (para o próximo turno)
1. Resolver autenticação git para push dos 4 commits acumulados
2. Considerar remover framer-motion de HeroParallaxDemo também (último componente que usa)
3. Se removido de todo o projeto: uninstall framer-motion do package.json (-73KB vendor chunk eliminado)
4. Lighthouse audit mobile para medir impacto cumulativo

## Última Atualização
2026-03-09T09:15:00-03:00
