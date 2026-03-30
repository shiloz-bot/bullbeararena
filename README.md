# BullBearArena 🐃🐻

**AI-powered stock analysis through legendary investor perspectives.**

Enter a ticker symbol. Watch five legendary investors debate the stock. Get a comprehensive analysis in seconds.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)

---

## 🎬 Demo

```
╭────────────────────────────────────────────────────────╮
│        🏟️ Apple Inc. — BullBearArena Analysis          │
│                  (AAPL | 10-K FY2025)                   │
╰────────────────────────────────────────────────────────╯

┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Agent       ┃ Rating     ┃ Confidence ┃ Verdict      ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 🤵 Buffett  │ Buy        │ 85%        │ Exceptional  │
│ 👩 Wood      │ Hold       │ 60%        │ Innovation   │
│ 🧑 Dalio    │ Buy        │ 70%        │ Macro tail   │
│ 🧐 Burry    │ Sell       │ 75%        │ Overvalued   │
│ 👨 Lynch    │ Buy        │ 80%        │ PEG attract. │
└─────────────┴────────────┴────────────┴──────────────┘

📈 Overall Score: 68/100 — Bullish 🐂🐂
```

## ✨ Features

- **🤖 5 Legendary Investor Agents** — Each with a unique investment philosophy and analysis style
- **📊 SEC EDGAR Data** — Free, real-time financial data (no API key needed)
- **⚔️ Debate-Style Reports** — Watch agents agree and disagree on key topics
- **🏛️ Roundtable Summary** — AI-generated narrative of the investor discussion
- **🌐 Web Dashboard** — Beautiful dark-themed UI with score rings, agent cards, and debate sections
- **💻 CLI Interface** — Analyze stocks from the terminal with rich formatting
- **🔌 Multi-LLM Support** — Works with OpenAI, Anthropic, Ollama, OpenRouter, and more

## 🧠 Meet the Investors

| Agent | Style | Focus |
|-------|-------|-------|
| 🤵 **Warren Buffett** | Value Investing | Moats, ROE, free cash flow |
| 👩 **Cathie Wood** | Disruptive Innovation | 5-year horizons, exponential growth |
| 🧑 **Ray Dalio** | Macro Cycle | Economic machine, debt cycles |
| 🧐 **Michael Burry** | Deep Value / Contrarian | Hidden risks, market mispricing |
| 👨 **Peter Lynch** | Pragmatic Growth | PEG ratio, "buy what you know" |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An LLM API key (OpenAI, Anthropic, or OpenRouter)

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/bullbeararena.git
cd bullbeararena
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -e .

# Configure
cp .env.example .env
# Edit .env and add your LLM_API_KEY
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Run

**Option A: Docker Compose (easiest)**

```bash
docker compose up
```

**Option B: Manual**

```bash
# Terminal 1 — Backend
cd backend
source venv/bin/activate
uvicorn app.api.app:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and search for a stock!

### 5. CLI Usage

```bash
cd backend
source venv/bin/activate

# Analyze a stock
bullbeararena analyze AAPL

# Use specific agents
bullbeararena analyze TSLA --agents buffett,burry

# Use Ollama (local, free)
bullbeararena analyze NVDA --provider ollama --model llama3

# Save report to file
bullbeararena analyze MSFT --output msft_report.md
```

## 🏗️ Architecture

```
User Input (ticker)
        │
        ▼
┌──────────────────┐
│  SEC EDGAR API    │ ← Free financial data
│  (no API key)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Metrics Engine   │ ← 30+ financial indicators
│  (Python)         │
└────────┬─────────┘
         │
    ┌────┼────┬─────┬─────┐
    ▼    ▼    ▼     ▼     ▼    ← Parallel LLM calls
  🤵    👩    🧑    🧐    👨
Buffett Wood Dalio Burry Lynch
    │    │    │     │     │
    └────┼────┴─────┴─────┘
         │
         ▼
┌──────────────────┐
│  Report Generator │ ← Debate + consensus + scoring
│  (LLM)            │
└────────┬─────────┘
         │
         ▼
  Web Dashboard / CLI / Markdown
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, FastAPI, Pydantic |
| Frontend | Next.js 15, React 19, Tailwind CSS 4 |
| AI/LLM | LiteLLM (OpenAI, Anthropic, Ollama, OpenRouter) |
| Data | SEC EDGAR API (free), Yahoo Finance |
| CLI | Typer, Rich |

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Analyze a stock |
| `GET` | `/api/agents` | List available agents |
| `GET` | `/api/ticker/{ticker}` | Look up ticker info |
| `GET` | `/api/health` | Health check |

### Example Request

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

## 💰 Cost

| Item | Cost |
|------|------|
| SEC EDGAR financial data | **Free** |
| Yahoo Finance stock prices | **Free** |
| LLM per analysis (GPT-4o-mini) | ~$0.05-0.15 |
| LLM per analysis (Ollama local) | **Free** |

## 🗺️ Roadmap

- [ ] **v0.1** — MVP with 5 agents, CLI + Web, SEC data
- [ ] **v0.2** — 3 more agents (Soros, Graham, Druckenmiller)
- [ ] **v0.3** — Historical backtesting
- [ ] **v0.4** — Earnings call transcript analysis
- [ ] **v0.5** — A-share & HK stock support
- [ ] **v0.6** — Discord/Telegram bot integration
- [ ] **v0.7** — Portfolio tracking and alerts

## 🤝 Contributing

Contributions are welcome! Especially:

- New investor agent personas
- Additional data sources (international markets)
- UI improvements and new chart types
- Bug fixes and test coverage

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⚠️ Disclaimer

**This project is for educational and entertainment purposes only.**

- Not financial, investment, or trading advice
- No guarantees on analysis accuracy
- Past performance does not indicate future results
- Always do your own research and consult a qualified financial advisor
- The "investor agents" simulate perspectives based on public information — they are not affiliated with the actual investors

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with 🐃🐻 and <a href="https://github.com/openclaw/openclaw">OpenClaw</a>
</p>
