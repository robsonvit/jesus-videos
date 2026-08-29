# 🙏 CRIAÇÃO VÍDEOS JESUS

Bot de geração automática de vídeos motivacionais cristãos para YouTube Shorts, TikTok e Reels.

Baseado na estrutura do projeto CRIAÇÃO VÍDEOS PORRADA.

## ⚙️ O que precisa ser personalizado

> **PENDENTE — aguardando configurações do usuário:**

| Item | Arquivo | O que mudar |
|------|---------|-------------|
| 📝 Script de geração de roteiro | scripts/gerar_roteiro.py | Temas, system prompt, estilo da narração |
| 🎙️ Voz | scripts/gerar_voz.py | FISH_VOICE_ID ou voz Kokoro usada |
| 🎬 Cenas iniciais (0-3s) | scripts/montar_video.py ou scripts/pipeline.py | Pasta/clips de abertura (substituir SHELBY) |
| 📺 Canal do YouTube | youtube_credentials.json + Secrets GitHub | Credenciais OAuth do canal correto |

## 🚀 Como rodar

### GitHub Actions (automático)
1. Configure os Secrets no repositório:
   - `FISH_API_KEY`
   - `OPENROUTER_API_KEY`
   - `PEXELS_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`

2. Disparo manual: Actions → 🎬 Gerar Vídeo JESUS → Run workflow
3. Agendado: todo dia às 09h (horário de Brasília)

## 🗂️ Estrutura
```
scripts/
  pipeline.py          → Orquestrador principal
  gerar_roteiro.py     → ⬅️ PERSONALIZAR: temas e prompt
  gerar_voz.py         → ⬅️ PERSONALIZAR: voz
  buscar_videos_pexels.py → Busca clips de fundo
  montar_video.py      → ⬅️ PERSONALIZAR: cenas 0-3s
  enviar_telegram.py   → Notificação Telegram
  enviar_youtube.py    → Upload YouTube
.github/workflows/
  gerar_video.yml      → Pipeline automático
musicas/               → MP3s de fundo (opcional)
CLIPES INICIAIS/       → ⬅️ Pasta a criar com os clips dos 3s iniciais
```