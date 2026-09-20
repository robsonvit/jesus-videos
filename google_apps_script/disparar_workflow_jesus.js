/**
 * ============================================================
 * DISPARAR WORKFLOW JESUS — Google Apps Script
 * ============================================================
 * 
 * COMO CONFIGURAR:
 * 1. Acesse: https://script.google.com/
 * 2. Crie um novo projeto e cole este código
 * 3. Gere um Personal Access Token (PAT) no GitHub:
 *    → Acesse: https://github.com/settings/tokens
 *    → Clique em "Generate new token (classic)"
 *    → Marque o escopo: "workflow"
 *    → Copie o token gerado (ghp_...)
 * 4. Cole o token na variável GITHUB_TOKEN abaixo
 * 5. Salve o script (Ctrl+S)
 * 6. Na aba "Acionadores" (ícone de relógio), configure:
 *    → Função: dispararVideoJesus
 *    → Tipo: Time-driven (por tempo)
 *    → Frequência desejada (ex: todo dia às 9h)
 * 
 * PARA TESTAR MANUALMENTE:
 *    → Selecione a função dispararVideoJesus e clique em "Executar"
 * ============================================================
 */

// ── CONFIGURAÇÕES — EDITE AQUI ────────────────────────────────────────────────
var GITHUB_TOKEN    = "ghp_COLE_SEU_TOKEN_AQUI";  // ← Cole seu PAT aqui
var REPO_OWNER      = "robsonvit";
var REPO_NOME       = "jesus-videos";
var WORKFLOW_ID     = "345015152";                  // ID do workflow 🙏 Gerar Vídeo JESUS
var NUM_VIDEOS      = "1";                          // Quantos vídeos gerar (1, 2, 3, 5 ou 10)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Função principal: dispara o workflow do GitHub Actions.
 * Configure esta função como acionador automático.
 */
function dispararVideoJesus() {
  var url = "https://api.github.com/repos/" + REPO_OWNER + "/" + REPO_NOME + 
            "/actions/workflows/" + WORKFLOW_ID + "/dispatches";

  var payload = JSON.stringify({
    "ref": "main",
    "inputs": {
      "num_videos": NUM_VIDEOS
    }
  });

  var opcoes = {
    "method": "POST",
    "headers": {
      "Authorization": "Bearer " + GITHUB_TOKEN,
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json"
    },
    "payload": payload,
    "muteHttpExceptions": true
  };

  try {
    var resposta = UrlFetchApp.fetch(url, opcoes);
    var status = resposta.getResponseCode();

    if (status === 204) {
      console.log("✅ Workflow disparado com sucesso! Status: " + status);
      Logger.log("✅ Workflow JESUS disparado com sucesso em: " + new Date());
    } else {
      var corpo = resposta.getContentText();
      console.log("❌ Erro ao disparar workflow. Status: " + status);
      console.log("Resposta: " + corpo);
      Logger.log("❌ ERRO " + status + ": " + corpo);
    }
  } catch (e) {
    console.log("❌ Exceção: " + e.toString());
    Logger.log("❌ Exceção ao chamar API GitHub: " + e.toString());
  }
}

/**
 * Função de diagnóstico: verifica se o token e as configurações estão corretos.
 * Execute esta função ANTES de configurar os acionadores automáticos.
 */
function testarConexao() {
  var url = "https://api.github.com/repos/" + REPO_OWNER + "/" + REPO_NOME + "/actions/workflows";

  var opcoes = {
    "method": "GET",
    "headers": {
      "Authorization": "Bearer " + GITHUB_TOKEN,
      "Accept": "application/vnd.github+json"
    },
    "muteHttpExceptions": true
  };

  var resposta = UrlFetchApp.fetch(url, opcoes);
  var status = resposta.getResponseCode();
  var dados = JSON.parse(resposta.getContentText());

  if (status === 200) {
    Logger.log("✅ Conexão OK! Workflows encontrados no repositório:");
    dados.workflows.forEach(function(wf) {
      Logger.log("  → [" + wf.id + "] " + wf.name + " (" + wf.state + ")");
    });
  } else {
    Logger.log("❌ Erro de autenticação. Status: " + status);
    Logger.log("Verifique se seu GITHUB_TOKEN está correto e tem permissão 'workflow'.");
  }
}
