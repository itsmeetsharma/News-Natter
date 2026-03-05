# 🤖 AI Roast Brief

Daily AI news digest. 5 stories. Medium roast. Delivered to your inbox at 7 AM IST.

## Stack
- **CrewAI** — multi-agent news pipeline
- **Groq** (Llama 3.3 70B) — LLM, falls back to Gemini 2.0 Flash
- **Serper** — web search for today's news
- **Imgflip** — meme generation per story
- **Resend** — email delivery
- **GitHub Actions** — cron scheduler (no server needed)

## 6 Rotating Visual Styles
| Day | Style | Vibe |
|-----|-------|------|
| Mon | NEWSPAPER | NYT energy, black/white/red |
| Tue | MEME | Impact font, chaos energy |
| Wed | COMIC | Robot character, speech bubbles |
| Thu | STARTUP | Clean, investor-deck vibes |
| Fri | TERMINAL | Green monospace, hacker aesthetic |
| Sat | MAGAZINE | Editorial Wired/Vox feel |

Gemini picks the best style based on that day's news vibe. Day-of-week is just the fallback.

## Setup

### 1. Clone and install
```bash
git clone https://github.com/YOURUSERNAME/ai-roast-brief
cd ai-roast-brief
pip install -r requirements.txt
```

### 2. Add API keys
```bash
cp .env.example .env
# Edit .env with your keys
```

### 3. Test locally
```bash
# Full dry run (no API calls for research, no email sent)
python main.py --test --dry-run

# Then open output.html in browser to preview

# Full run with real news but no email
python main.py --dry-run

# Force a specific style
python main.py --test --dry-run --style TERMINAL
```

### 4. Add secrets to GitHub
Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add all keys from `.env.example`:
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `SERPER_API_KEY`
- `RESEND_API_KEY`
- `EMAIL_FROM` (e.g. `AI Roast Brief <brief@yourdomain.com>`)
- `EMAIL_TO` (your email, comma-separated for multiple)
- `IMGFLIP_USERNAME`
- `IMGFLIP_PASSWORD`

### 5. Push and activate
```bash
git add .
git commit -m "init: ai roast brief"
git push
```

GitHub Actions runs automatically at **01:30 UTC = 7:00 AM IST** every day.

To trigger manually: Actions tab → Daily Brief → Run workflow.

## API Keys (all free)
| Service | Where to get | Free tier |
|---------|-------------|-----------|
| Groq | console.groq.com | 14,400 req/day |
| Gemini | aistudio.google.com | Generous free |
| Serper | serper.dev | 100 searches/month |
| Resend | resend.com | 3,000 emails/month |
| Imgflip | imgflip.com | Free, public memes |

## Project Structure
```
├── main.py                  # Entry point
├── agents/
│   ├── researcher.py        # Serper search agent
│   ├── writer.py            # Groq LLM, roast writer
│   ├── email_builder.py     # HTML email with 6 themes
│   └── sender.py            # Resend delivery
├── utils/
│   ├── llm.py               # Groq + Gemini fallback
│   └── meme.py              # Imgflip meme generator
├── .github/workflows/
│   └── daily.yml            # GitHub Actions cron
├── episode.txt              # Auto-incremented episode counter
└── .env.example             # API keys template
```
