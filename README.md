<div align="center">

# 🤖 AI Roast Brief

**Daily AI news digest. 5 stories. Medium roast. In your inbox at 7 AM.**

[![Daily Brief](https://github.com/YOURUSERNAME/ai-roast-brief/actions/workflows/daily.yml/badge.svg)](https://github.com/YOURUSERNAME/ai-roast-brief/actions/workflows/daily.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Cost](https://img.shields.io/badge/running%20cost-₹0%2Fmonth-brightgreen)

</div>

---

## What It Does

Every morning at 7 AM IST, this runs automatically on GitHub Actions:

1. **Searches** the web for today's top AI news via Serper
2. **Writes** a roast-style brief using Groq (Llama 3.3 70B) with Gemini as fallback
3. **Generates** a meme for each story via Imgflip
4. **Sends** a styled HTML email to your inbox via Resend

No servers. No dashboards. No subscriptions. Just an email every morning.

---

## 6 Rotating Visual Styles

The LLM picks the best style based on that day's news vibe. Day-of-week is the fallback.

| Day | Style | Aesthetic |
|-----|-------|-----------|
| Mon | `NEWSPAPER` | NYT serif · black, white, editorial red |
| Tue | `MEME` | Impact font · dark background · chaos energy |
| Wed | `COMIC` | Speech bubbles · robot character · panels |
| Thu | `STARTUP` | Clean white · Helvetica · investor deck |
| Fri | `TERMINAL` | Green monospace · CRT aesthetic · hacker energy |
| Sat | `MAGAZINE` | Georgia serif · Wired/Vox editorial layout |

---

## Stack

| Purpose | Tool | Why |
|---------|------|-----|
| LLM (primary) | [Groq](https://console.groq.com) — Llama 3.3 70B | Fastest free inference |
| LLM (fallback) | [Gemini](https://aistudio.google.com) — 2.0 Flash | Auto-switches if Groq fails |
| Web search | [Serper](https://serper.dev) | Google results via API |
| Memes | [Imgflip](https://imgflip.com) | Captions real meme templates |
| Email | [Resend](https://resend.com) | Dead-simple transactional email |
| Scheduler | GitHub Actions | Free, zero infrastructure |

---

## Project Structure

```
ai-roast-brief/
│
├── main.py                    # Entry point — orchestrates the full pipeline
│
├── agents/
│   ├── researcher.py          # Serper search → LLM summarization
│   ├── writer.py              # Structures brief as JSON with roast tone
│   ├── email_builder.py       # Assembles HTML email with 6 theme support
│   └── sender.py              # Resend API delivery
│
├── utils/
│   ├── llm.py                 # Groq + Gemini fallback wrapper
│   └── meme.py                # Imgflip template picker + caption generator
│
├── .github/
│   └── workflows/
│       └── daily.yml          # GitHub Actions cron — runs at 01:30 UTC (7 AM IST)
│
├── episode.txt                # Auto-incremented episode counter
├── requirements.txt
├── .env.example               # API keys template
└── .gitignore
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOURUSERNAME/ai-roast-brief
cd ai-roast-brief
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` with your keys (all free tier):

```env
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
SERPER_API_KEY=your_key_here
RESEND_API_KEY=your_key_here
EMAIL_FROM=onboarding@resend.dev
EMAIL_TO=you@gmail.com
IMGFLIP_USERNAME=your_username
IMGFLIP_PASSWORD=your_password
```

### 3. Test locally

```bash
# Step 1 — fake news, no email, just renders output.html
python main.py --test --dry-run

# Step 2 — real news from Serper, still no email
python main.py --dry-run

# Step 3 — full run, email sent
python main.py
```

### 4. Deploy to GitHub Actions

```bash
git add .
git commit -m "init: ai roast brief"
git push -u origin main
```

Then add your secrets at **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `GROQ_API_KEY` | From console.groq.com |
| `GEMINI_API_KEY` | From aistudio.google.com |
| `SERPER_API_KEY` | From serper.dev |
| `RESEND_API_KEY` | From resend.com |
| `EMAIL_FROM` | e.g. `onboarding@resend.dev` |
| `EMAIL_TO` | Your email address |
| `IMGFLIP_USERNAME` | Your Imgflip username |
| `IMGFLIP_PASSWORD` | Your Imgflip password |

Trigger a manual test: **Actions → AI Roast Brief — Daily → Run workflow**

After that it runs every day at **7:00 AM IST** automatically.

---

## CLI Options

```bash
python main.py                          # Full run
python main.py --test                   # Use fake news (saves Serper quota)
python main.py --dry-run                # Build email, save to output.html, don't send
python main.py --style TERMINAL         # Force a specific style
python main.py --test --dry-run         # Fastest local test, zero API calls
```

---

## Free Tier Limits

| Service | Free Tier | Usage |
|---------|-----------|-------|
| Groq | 14,400 req/day | ~10 req/run |
| Gemini | 1,500 req/day | Fallback only |
| Serper | 2,500 searches/month | 4/day = ~120/month |
| Resend | 3,000 emails/month | 1/day = 30/month |
| Imgflip | Unlimited | 5 memes/run |
| GitHub Actions | 2,000 min/month | ~2 min/run = 60/month |

**Total cost: ₹0/month**

---

## License

MIT — do whatever you want with it.
