# 🎯 Quick Start Guide - AFCON Chatbot

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies (1 min)
```bash
pip install -r requirements.txt
```

### Step 2: Configure API Key (1 min)
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Setup Vector Store (2 min)
```bash
python scripts/setup_vectorstore.py
```

### Step 4: Start Server (30 sec)
```bash
python -m src.api.server
```

### Step 5: Use Chatbot (now!)
```bash
# Option A: Web Interface
# Open frontend/index.html in your browser

# Option B: CLI
python scripts/run_cli.py

# Option C: API
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who won AFCON 2025?"}'
```

---

## 🎨 Visual Quick Reference

### System Architecture (Simple View)
```
┌─────────────────────────────────────────────┐
│             USER INTERFACE                   │
│  Web UI  │  CLI Tool  │  REST API           │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│          FastAPI Server :8000                │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│          AFCON Chatbot                       │
│        Query Dispatcher                      │
└──────────┬────────────────┬─────────────────┘
           ↓                ↓
    ┌──────────┐      ┌──────────┐
    │   LIVE   │      │   RAG    │
    │   DATA   │      │  MODULE  │
    └──────────┘      └──────────┘
         ↓                  ↓
    ESPN API          Vector Store
                       (FAISS + GPT-4)
```

### Query Flow
```
1. User asks: "Who scored for Morocco?"
              ↓
2. Dispatcher classifies: "historical query"
              ↓
3. Retriever searches vector store
              ↓
4. RAG chain generates answer with GPT-4
              ↓
5. User gets: "Brahim Díaz scored in the 55th minute..."
```

---

## 📁 Key Files Reference

### Configuration Files
```
.env              → Your API keys (create from .env.example)
config.py         → Application settings
requirements.txt  → Python dependencies
```

### Main Modules
```
src/chatbot/chatbot.py      → Main orchestrator
src/api/server.py           → FastAPI endpoints
src/live_data/api_client.py → ESPN API
src/rag/rag_chain.py        → RAG implementation
```

### Utility Scripts
```
quickstart.py                    → Complete setup
scripts/test_system.py           → Verify installation
scripts/run_cli.py               → Chat in terminal
scripts/setup_vectorstore.py     → Create embeddings
```

### Interfaces
```
frontend/index.html          → Web chat UI
scripts/run_cli.py          → Terminal interface
http://localhost:8000/docs  → API documentation
```

---

## 💬 Example Queries

### For Live Matches
```
"What's the current score?"
"Who scored in the latest match?"
"Show me live updates for Morocco"
```

### For History
```
"Who has won the most AFCON titles?"
"Tell me about the 2019 tournament"
"Which teams qualified for the semifinals?"
```

### For Statistics
```
"What was Morocco's possession percentage?"
"Compare shots on target"
"Show me passing accuracy stats"
```

---

## 🛠️ Common Commands

### Development
```bash
# Start server with auto-reload
python -m src.api.server

# Or with uvicorn directly
uvicorn src.api.server:app --reload

# Run CLI interface
python scripts/run_cli.py

# Test system
python scripts/test_system.py
```

### Data Operations
```bash
# Process new match data
python scripts/run_etl.py <event_id>

# Monitor live match
python scripts/monitor_live_match.py <event_id>

# Rebuild vector store
python scripts/setup_vectorstore.py
```

### Server Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question"}'

# Set live match
curl -X POST http://localhost:8000/live/set \
  -H "Content-Type: application/json" \
  -d '{"event_id": "732133"}'
```

---

## 🔧 Troubleshooting

### "ModuleNotFoundError"
```bash
# Install dependencies
pip install -r requirements.txt
```

### "Vector store not found"
```bash
# Create the vector store
python scripts/setup_vectorstore.py
```

### "OpenAI API error"
```bash
# Check your .env file has valid API key
# Format: OPENAI_API_KEY=sk-...
```

### "Port 8000 already in use"
```bash
# Change port in .env
PORT=8080

# Or specify when running
uvicorn src.api.server:app --port 8080
```

---

## 📊 Project Status

✅ **Implemented**: All core features
✅ **Tested**: System verification complete
✅ **Documented**: Comprehensive guides
✅ **Ready**: Production-ready code

---

## 🎯 Next Steps After Setup

1. **Try the web interface**: Open `frontend/index.html`
2. **Explore the API docs**: Visit `http://localhost:8000/docs`
3. **Test different queries**: Try live, historical, and statistical questions
4. **Add more data**: Place CSV files in `data/historical/` and re-run setup
5. **Customize**: Edit prompts in `src/rag/rag_chain.py`

---

## 📚 Documentation Index

- **README.md** - Overview and features
- **SETUP.md** - Detailed setup instructions
- **ARCHITECTURE.md** - Technical architecture
- **PROJECT_SUMMARY.md** - Implementation details
- **CHECKLIST.md** - Feature completeness
- **This file** - Quick reference

---

## 🆘 Need Help?

1. Check [SETUP.md](SETUP.md) for detailed instructions
2. Review error messages carefully
3. Verify all prerequisites are installed
4. Check API documentation at `/docs`
5. Review example queries above

---

**🎉 You're all set! Start chatting about AFCON!**
