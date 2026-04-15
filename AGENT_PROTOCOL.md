# AGENT_PROTOCOL.md — Protocolo de Trabalho dos Agentes

## Lei Fundamental
**Nenhum agente pode encerrar seu turno sem produzir um entregável concreto.**

"Entregável" = arquivo salvo, código commitado, texto escrito, análise documentada, ou tarefa marcada como done com evidência.

## Ciclo de Turno (obrigatório)

### 1. CARREGAR CONTEXTO (primeiros 30s)
```
Ler: /root/clawd/agent_worklog/<agent_id>.md
```
Este arquivo contém:
- Tarefa atual e seu status
- Progresso da última sessão
- Próximos passos pendentes
- Arquivos modificados

Se o arquivo não existe, é o primeiro turno — começar do zero.

### 2. EXECUTAR TRABALHO (bulk do turno)
- Pegar UMA tarefa por vez (não duas)
- Trabalhar nela até conclusão OU até restar 20% do timeout
- Cada ação deve produzir um artefato em disco (arquivo, commit, etc.)

### 3. SALVAR ESTADO (últimos 60s — OBRIGATÓRIO)
Antes de encerrar, SEMPRE atualizar `/root/clawd/agent_worklog/<agent_id>.md`:

```markdown
# Worklog: <Agent Name>
## Tarefa Atual
- ID: <task_id>
- Título: <título>
- Status: in_progress | done | blocked

## Progresso
- [x] Passo 1 concluído
- [x] Passo 2 concluído
- [ ] Passo 3 pendente

## Arquivos Modificados
- /path/to/file1.jsx — descrição da mudança
- /path/to/file2.py — descrição da mudança

## Próximos Passos (para o próximo turno)
1. Fazer X
2. Fazer Y

## Última Atualização
<timestamp ISO>
```

### 4. REPORTAR (após salvar)
- Registrar resumo diretamente no Notion (board/página da tarefa)
- Se tarefa concluída: marcar como done no Notion (via API interna /api/tasks)

## Regras de Ouro

1. **Tarefa pequena > tarefa grande.** Se uma tarefa leva mais de 1 turno, decomponha em sub-tarefas.
2. **Arquivo > memória.** Tudo que importa vai pro disco. Sessão morre, arquivo fica.
3. **Done = evidência.** "Terminei" sem arquivo/commit/link = não terminou.
4. **Blocked = especifique.** Se bloqueado, diga exatamente O QUÊ bloqueia e QUEM pode desbloquear.
5. **Um agente, uma tarefa.** Não pegue 3 tarefas e não termine nenhuma.

## Exemplo: Estaleiro (Frontend)

**Turno bom:**
```
1. Leu worklog → tarefa: "Revisar hero section Meraki"
2. Editou /root/clawd/meraki-glow-design/src/components/Hero.jsx
3. Rodou build, sem erros
4. Commitou: "feat: redesign hero section com CTA prominence"
5. Atualizou worklog com próximos passos: "ajustar responsivo mobile"
6. Postou no Feed: "Hero section redesenhada, commit abc123"
7. Se terminou tudo: marcou tarefa como done
```

**Turno ruim:**
```
1. Leu board do Notion
2. Viu 3 tarefas in_progress
3. Analisou todas superficialmente
4. Não editou nenhum arquivo
5. Sessão morreu
→ Zero entregável. Turno desperdiçado.
```

## Para o Jarvis (Coordenador)

Jarvis NÃO executa tarefas técnicas. Jarvis:
1. Lê todos os worklogs dos agentes
2. Identifica bloqueios e dependências
3. Redistribui tarefas se necessário
4. Decompõe tarefas grandes em sub-tarefas atômicas
5. Garante que cada agente tem exatamente 1 tarefa clara

## Sistema de Tarefas (Notion via API interna)

> Importante: `/api/tasks` é o endpoint interno que espelha o board do Notion. Não tratar como kanban legado.

### Consultar suas tarefas
No início de cada turno, consulte suas tarefas atribuídas no Notion:
```bash
curl -s http://127.0.0.1:8001/api/tasks | python3 -c "import sys,json; [print(json.dumps(t,ensure_ascii=False)) for t in json.load(sys.stdin)['tasks'] if t.get('agent')=='<SEU_AGENT_NAME>' and t.get('status') in ('todo','in_progress')]"
```

Substitua `<SEU_AGENT_NAME>` pelo seu nome de agente (jarvis, designer, estaleiro, etc.)

### Marcar tarefa como concluída
Quando terminar uma tarefa:
```bash
curl -s http://127.0.0.1:8001/api/tasks -X POST \
  -H 'Content-Type: application/json' \
  -d '{"title":"<título_original>","agent":"<seu_agent>","status":"done"}'
```

### Atualizar status para in_progress
Quando começar a trabalhar numa tarefa:
```bash
curl -s http://127.0.0.1:8001/api/tasks -X POST \
  -H 'Content-Type: application/json' \
  -d '{"title":"<título_original>","agent":"<seu_agent>","status":"in_progress"}'
```

### Exemplo Prático - Designer
```bash
# 1. Consultar tarefas
curl -s http://127.0.0.1:8001/api/tasks | python3 -c "import sys,json; [print(json.dumps(t,ensure_ascii=False)) for t in json.load(sys.stdin)['tasks'] if t.get('agent')=='designer' and t.get('status') in ('todo','in_progress')]"

# 2. Trabalhar na tarefa...

# 3. Ao concluir
curl -s http://127.0.0.1:8001/api/tasks -X POST \
  -H 'Content-Type: application/json' \
  -d '{"title":"Criar identidade visual Meraki Group","agent":"designer","status":"done"}'
```

## Registro no Notion

O resumo do turno deve ser salvo no próprio Notion (na tarefa correspondente e/ou página operacional do agente), sem uso de Feed separado.
