# Meraki Group — Typography Rhythm Guide

## Objetivo
Aprimorar consistência de leitura e sensação premium com ritmo tipográfico previsível para páginas comerciais.

## Font Stack (mantido)
- Display: `Playfair Display`, serif
- Body/UI: `Inter`, sans-serif

## Escala Tipográfica (desktop-first)
- `display-xl`: 64/72, 700, -0.02em
- `display-lg`: 52/60, 700, -0.02em
- `h1`: 44/52, 700, -0.015em
- `h2`: 34/42, 700, -0.01em
- `h3`: 28/36, 650, -0.005em
- `h4`: 22/30, 650, 0
- `body-lg`: 20/32, 400, 0
- `body-md`: 18/30, 400, 0
- `body-sm`: 16/26, 400, 0.002em
- `label`: 14/20, 600, 0.015em
- `caption`: 12/18, 500, 0.02em

## Escala Mobile (<=768px)
- `display-xl`: 44/52
- `display-lg`: 38/46
- `h1`: 34/42
- `h2`: 28/36
- `h3`: 24/32
- `h4`: 20/28
- `body-lg`: 18/28
- `body-md`: 16/26
- `body-sm`: 15/24

## Regras de Ritmo
1. **Máximo de 2 famílias** por página (já definido acima).
2. **Parágrafos longos:** usar `body-md` com largura de 60–72 caracteres.
3. **Espaçamento vertical:**
   - Título → subtítulo: 12–16px
   - Subtítulo → parágrafo: 12px
   - Parágrafo → CTA: 20–24px
4. **Evitar blocos all-caps** em textos acima de 20 caracteres.
5. **Peso visual de CTA:** label 600, tracking +0.015em, min-height 48px.

## Aplicação por Seção
### Hero
- Headline: `h1` (desktop) / `h2` (mobile), Display
- Subheadline: `body-lg`, Inter
- CTA primário: `label`

### Benefícios
- Título seção: `h2`
- Título card: `h4`
- Texto card: `body-sm`

### Proposta
- Título seção: `h2`
- Blocos de valor: `body-md` + destaques em 600

### Contato
- Título seção: `h3`
- Labels formulário: `label`
- Ajuda/erro: `caption`

## Checklist Rápido
- [ ] Headings seguem hierarquia sem pular níveis
- [ ] Nenhum body abaixo de 15px no mobile
- [ ] Line-height >= 1.45 em texto corrido
- [ ] CTA principal mantém contraste e legibilidade
