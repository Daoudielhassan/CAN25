# AFCON Chatbot Project 🏆⚽

AI-powered chatbot for African Cup of Nations (AFCON) with live updates and historical insights using RAG (Retrieval Augmented Generation).

## ✨ Features

- ⚡ **Live Match Updates**: Real-time scores, goals, and events from ESPN API
- 📚 **Historical Insights**: RAG-powered queries on AFCON history and statistics
- 💬 **Conversational AI**: Natural language interface with context awareness
- 🔍 **Smart Query Routing**: Automatic classification of live vs historical queries
- 📊 **Rich Statistics**: Team performance, player stats, and match analytics
- 🌐 **Multiple Interfaces**: Web UI, CLI, and REST API

## 🏗️ Architecture

```
src/
├── live_data/       # ESPN API client, ETL, live match monitoring
├── knowledge_base/  # Historical data loading and vector storage (FAISS)
├── rag/            # Retrieval system and RAG chains
├── chatbot/        # Query dispatcher and chatbot orchestration
└── api/            # FastAPI server with REST endpoints

data/
├── historical/     # CSV historical AFCON data
└── vector_store/   # FAISS embeddings database

frontend/           # Modern web interface
scripts/            # Setup and utility scripts
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Setup Vector Store
```bash
python scripts/setup_vectorstore.py
```

This will:
- Move CSV files to `data/historical/`
- Create embeddings using OpenAI
- Build FAISS vector database

### 4. Test the System
```bash
python scripts/test_system.py
```

### 5. Start the Server
```bash
python -m src.api.server
```

### 6. Use the Chatbot

**Web Interface** (Recommended):
```bash
# Open frontend/index.html in your browser
```

**CLI Interface**:
```bash
python scripts/run_cli.py
```

**API**:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who scored for Morocco?"}'
```

## 📖 Detailed Setup

See [SETUP.md](SETUP.md) for comprehensive setup instructions, troubleshooting, and configuration options


## 🛠️ Technology Stack

| Layer | Technologies |
|-------|-------------|
| **AI/LLM** | OpenAI GPT-4 Turbo, text-embedding-3-small |
| **RAG** | LangChain, FAISS vector database |
| **Backend** | FastAPI, Uvicorn |
| **Data** | Pandas, Requests, Pydantic |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **APIs** | ESPN AFCON API |

## 📝 Usage Examples

### Live Match Queries
```
"What's the current score?"
"Who scored in the Morocco match?"
"Show me live updates for event 732133"
```

### Historical Queries
```
"Which team has won the most AFCON titles?"
"Who scored for Morocco vs Comoros in 2025?"
"What were Egypt's results in the 2019 tournament?"
```

### Statistical Queries
```
"What was Morocco's possession percentage?"
"Compare shots on target between Senegal and Nigeria"
"Show me passing accuracy statistics"
```

## 🔧 Utility Scripts

| Script | Purpose |
|--------|---------|
| `scripts/test_system.py` | Verify all system components |
| `scripts/setup_vectorstore.py` | Initialize vector database |
| `scripts/run_cli.py` | Launch CLI chatbot |
| `scripts/run_etl.py` | Process match data to CSV |
| `scripts/monitor_live_match.py` | Watch live match updates |

## 🌐 API Endpoints

Full API documentation available at `http://localhost:8000/docs` when server is running.

**Key Endpoints:**
- `POST /chat` - Chat with the bot
- `POST /live/set` - Set live match to monitor
- `POST /match/summary` - Get match details
- `GET /health` - Health check

## 📊 Data Pipeline

```
ESPN API → ETL Processor → CSV Files → Data Loader → Embeddings → FAISS Vector Store
                ↓                                                        ↓
         Live Data Module                                          RAG Module
                ↓                                                        ↓
                       → Query Dispatcher → Chatbot → Response
```

## 🔐 Environment Variables

Configure in `.env`:
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `OPENAI_MODEL` - GPT model (default: gpt-4-turbo-preview)
- `EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-small)
- `REFRESH_INTERVAL` - Live update interval in seconds (default: 30)
- `PORT` - API server port (default: 8000)

## 🐛 Troubleshooting

**"Vector store not found"**
```bash
python scripts/setup_vectorstore.py
```

**"OpenAI API error"**
- Check your API key in `.env`
- Verify you have credits in your OpenAI account

**"No data loaded"**
- Ensure CSV files are in `data/historical/`
- Check file format matches expected structure

See [SETUP.md](SETUP.md) for more troubleshooting tips.

## 📈 Extending the System

### Add New Data Sources
1. Create CSV files in AFCON format
2. Place in `data/historical/`
3. Run `python scripts/setup_vectorstore.py`

### Add Custom Endpoints
Edit `src/api/server.py` and add new FastAPI routes.

### Customize RAG Prompts
Modify prompt templates in `src/rag/rag_chain.py`.

### Add New Query Types
Update `src/chatbot/dispatcher.py` with new classification logic.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional data sources (player stats, tournament history)
- Multi-language support
- Caching layer for performance
- Advanced analytics and visualizations
- Mobile app interface

## 📄 License

MIT License - See LICENSE file for details
