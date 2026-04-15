# Guideline rápido — Aplicação Digital vs Impressão (Meraki Proposal)

## Objetivo
Garantir consistência visual do template de proposta em dois contextos: visualização digital e envio impresso/PDF.

## Paleta
- **Digital (dark/light híbrido):** pode usar gradientes e sombras suaves para profundidade.
- **Impressão (light):** priorizar fundo branco e cores sólidas para previsibilidade de tinta.
- Azul primário recomendado: `#1D4ED8`.
- Evitar fundos escuros chapados em páginas longas para reduzir custo de impressão.

## Tipografia
- Títulos: `Playfair Display` (ou fallback Georgia no PDF sem embed).
- Corpo: `Inter` (ou fallback Segoe UI/Arial).
- Tamanho mínimo para impressão: 10.5–11pt no corpo.
- Linha recomendada: 1.45–1.6 para leitura confortável.

## Layout
- Margens impressão: mínimo 16mm.
- Grade sugerida: conteúdo principal em coluna única (A4), cards apenas para blocos curtos (planos e highlights).
- Evitar elementos muito próximos da dobra/corte.

## Contraste e legibilidade
- Garantir contraste AA mínimo entre texto e fundo.
- Em impressão, evitar texto colorido claro em fundo colorido.

## Exportação
- Formato principal: PDF (A4), com fontes incorporadas quando possível.
- Preview rápido: PNG 2x (para validação visual em chat e aprovações rápidas).

## Checklist de handoff
- [ ] Versão HTML final validada
- [ ] PDF exportado em A4
- [ ] PNG de preview gerado
- [ ] Tokens light e dark referenciados
