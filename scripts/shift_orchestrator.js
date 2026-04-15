const { execSync } = require('child_process');
const fs = require('fs');

const CONFIG_PATH = '/root/clawd/scripts/agents_config.json';

function delegateNewTasks(config) {
  const tasks = config.tasks || [];
  let changed = false;
  for (const t of tasks) {
    if (t.status !== 'in_progress') continue;
    if (t.delegated_at) continue;
    try {
      const msg = `Nova tarefa no Kanban para delegar: ${t.title} | id: ${t.id} | agente: ${t.agent || '—'}. Ao finalizar a delegação, marque a tarefa como done (task_done) usando o id.`;
      const cmd = `openclaw agent --agent jarvis --message "${msg}" --deliver &`;
      execSync(cmd);
      const feedText = `Jarvis delegou tarefa: ${t.title}\nPrompt usado: ${msg}`;
      try {
        execSync(`curl -s http://127.0.0.1:8001/api/feed -H 'Content-Type: application/json' -d '{"agent":"jarvis","type":"agent","text":"${feedText.replace(/"/g,'\\"')}"}'`);
      } catch (e) {}
      t.delegated_at = Date.now();
      changed = true;
    } catch (err) {
      console.error(`Erro delegando tarefa:`, err.message);
    }
  }
  return changed;
}

function checkAndWake() {
  if (!fs.existsSync(CONFIG_PATH)) return;

  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  const now = new Date();
  const currentTime = now.toISOString().substring(11, 16); 

  console.log(`[Shift] Checking for ${currentTime} UTC...`);

  const today = now.toISOString().substring(0,10);
  let touched = false;
  for (const agent of config.agents) {
    if (agent.enabled && agent.shift === currentTime) {
      console.log(`[Shift] Waking ${agent.name} with model ${agent.model}...`);
      try {
        let message = `Acorde, ${agent.name}. Inicie seu turno usando o modelo ${agent.model}. Verifique o Kanban.`;
        if (agent.id === 'estaleiro') {
          message += ' Obrigatório: sempre usar a skill UI/UX Pro Max para trabalhos de frontend.';
          message += ' Antes de marcar tarefa como done, fazer deploy na Netlify via CLI: netlify deploy --prod --site meragi-glow-design (usa os caminhos do Netlify).';
        }
        const cmd = `openclaw agent --agent ${agent.id} --message "${message}" --deliver &`;
        execSync(cmd);
        agent.last_wake_date = today;
        touched = true;
      } catch (err) {
        console.error(`Erro:`, err.message);
      }
    }
  }

  /* Desativado por solicitação do Eduardo: alertas de atraso
  for (const agent of config.agents) {
    if (!agent.enabled || !agent.shift) continue;
    if (agent.last_wake_date === today) continue;
    if (agent.last_alert_date === today) continue;
    const [h,m] = agent.shift.split(':').map(n=>parseInt(n,10));
    const shiftTime = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), h, m));
    if (now - shiftTime >= 10 * 60 * 1000) {
      const text = `Atraso no turno: ${agent.name} não acordou no horário (${agent.shift} UTC).`;
      try {
        execSync(`curl -s http://127.0.0.1:8001/api/feed -H 'Content-Type: application/json' -d '{"agent":"jarvis","type":"alert","text":"${text.replace(/"/g,'\\"')}"}'`);
        execSync(`curl -s http://127.0.0.1:8001/api/notify/telegram -H 'Content-Type: application/json' -d '{"text":"${text.replace(/"/g,'\\"')}","agent":"jarvis"}'`);
        agent.last_alert_date = today;
        touched = true;
      } catch (e) {}
    }
  }
  */

  const changed = delegateNewTasks(config);
  if (changed || touched) {
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
  }
}

checkAndWake();
