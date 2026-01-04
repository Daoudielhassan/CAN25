# AFCON 2025 Chatbot 🏆⚽

AI-powered conversational chatbot for African Cup of Nations 2025 with real-time updates, historical insights, and intelligent conversation memory using advanced RAG (Retrieval Augmented Generation).

## ✨ Key Features

- 🤖 **Agentic RAG**: LLM agent with tools for intelligent information retrieval
- 💬 **Conversational Memory**: Maintains context across conversation for natural follow-ups
- ⚡ **Live Match Data**: Real-time scores and events from ESPN API
- 📚 **Complete Historical Data**: 38 completed matches, 93 goals, 24 teams
- 🎯 **Semantic Routing**: Smart query classification using embeddings
- ⚡ **Redis Caching**: Fast response times with multi-level caching
- 🌐 **REST API**: FastAPI server with auto-generated docs
- 📊 **Rich Statistics**: Team performance, player stats, match details

## 🏗️ Architecture

**Système hybride intelligent combinant Traditional RAG (rapide) et Agentic RAG (précis)**

### Composants Clés

- **API Server** (FastAPI) - Gestion sessions & historique conversationnel
- **Chatbot Orchestrator** - Routage intelligent + détection questions de suivi
- **Dual RAG System**:
  - Traditional RAG: Vector store → LLM (< 1s, $0.001/requête)
  - Agentic RAG: Multi-outils avec ESPN API (3-5s, $0.005/requête)
- **Vector Store** (FAISS) - 376 documents historiques indexés
- **Cache Multi-Niveaux** - Redis (1h) + Fichier (24h)
- **Live Data** - Intégration ESPN API temps réel

### Flux de Données
```
User Query → Détection Suivi → Routage Sémantique
                                      ↓
                   ┌──────────────────┴──────────────────┐
                   ↓                                     ↓
            Traditional RAG                      Agentic RAG
         (données historiques)              (multi-sources + API)
                   ↓                                     ↓
              Redis Cache ←→ Vector Store ←→ ESPN API
                   ↓                                     ↓
                   └──────────────────┬──────────────────┘
                                      ↓
                              Response + Context
```

**📖 Documentation complète:** [ARCHITECTURE_TECHNIQUE.md](ARCHITECTURE_TECHNIQUE.md) (français)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Redis server
- Groq API key (free tier available)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
```

Get Groq API key: https://console.groq.com/keys

### 3. Start Redis
```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 --name afcon-redis redis:alpine

# Or install Redis locally
```

### 4. Build Vector Store
```bash
python scripts/setup_vectorstore.py
```

Expected output: 376 documents, 316 chunks
### 5. Start the Server
```bash
python run_server.py
```

Server starts on: http://0.0.0.0:8000
API docs: http://0.0.0.0:8000/docs

## 💬 Usage Examples

### Web Interface
Open `frontend/index.html` in your browser for a modern chat interface.

### API Examples
```bash
# Ask about top scorers
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who are the top scorers?", "session_id": "user123"}'

# Follow-up question (uses conversation history)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about the second player", "session_id": "user123"}'

# Get cache stats
curl "http://localhost:8000/cache/stats"

# Clear cache
curl -X POST "http://localhost:8000/cache/clear"
```

### Sample Conversations

**Top Scorers:**
- User: "Who are the top scorers?"
- Bot: "The top scorers are Ayoub El Kaabi (Morocco), Brahim Díaz (Morocco), Lassine Sinayoko (Mali), and Riyad Mahrez, all with 3 goals each."

**Follow-up Questions:**
- User: "In which matches did Brahim score?"
- Bot: "Brahim Díaz scored in Morocco vs Comoros (55'), Morocco vs Mali (45' penalty), and Zambia vs Morocco (27')."
- User: "Give me details about the second match"
- Bot: "Morocco vs Mali ended 1-1. Morocco won 3-1 on penalties in the Round of 16..."

**Team Statistics:**
- User: "How did Morocco perform?"
- Bot: "Morocco won Group F with 7 points, scoring 5 goals with 2 wins and 1 draw. They qualified for the Round of 16."

## 🛠️ Technology Stack

| Layer | Technologies |
|-------|-------------|
| **LLM** | Groq (llama-3.3-70b-versatile) |
| **Framework** | LangChain (Agentic RAG) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Vector Store** | FAISS (376 documents) |
| **Cache** | Redis (multi-niveaux) |
| **API** | FastAPI + Uvicorn |
| **Frontend** | HTML/CSS/JavaScript |
| **Data Source** | ESPN API (temps réel) |

## 📊 Data Coverage

- **Matches**: 38 completed (20 group stage + 18 knockout)
- **Goals**: 93 total goals scored
- **Teams**: 24 participating teams
- **Documents**: 376 in vector store
- **Last Updated**: January 4, 2026

## 🚀 Advanced Features

### Conversation Memory
The chatbot maintains conversation history per session:
```json
{
  "query": "Tell me about the second match",
  "session_id": "user123"
}
```

### Smart Follow-up Detection
Automatically detects references like:
- "the second match"
- "that team"
- "those players"
- "tell me more about it"

### Multi-level Caching
1. **Redis Cache**: Fast shared cache for common queries
2. **Memory Cache**: In-memory cache for recent queries
3. **TTL**: 1 hour for dynamic data, no expiry for static

### Semantic Routing
Uses embeddings to classify queries:
- Live data queries → ESPN API
- Historical queries → Vector store RAG
- Statistics queries → Enhanced RAG with aggregations

## 🔧 Key Scripts

| Script | Purpose |
|--------|---------|
| `run_server.py` | Start the FastAPI server |
| `fetch_all_afcon_data.py` | Fetch latest match data from ESPN |
| `scripts/setup_vectorstore.py` | Build/rebuild vector store |
| `quickstart.py` | Quick testing script |

## 🌐 API Endpoints

Documentation: `http://localhost:8000/docs`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send query with optional session_id |
| `/health` | GET | Check server health |
| `/cache/stats` | GET | Get cache statistics |
| `/cache/clear` | POST | Clear response cache |
| `/live/set` | POST | Set live match to monitor |

## 📚 Documentation

- **[ARCHITECTURE_TECHNIQUE.md](ARCHITECTURE_TECHNIQUE.md)** - Architecture complète (français)
- [DEPLOYMENT.md](DEPLOYMENT.md) - Guide de déploiement
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Checklist production
- [CODE_CLEANUP_SUMMARY.md](CODE_CLEANUP_SUMMARY.md) - Nettoyage du code

## 🐛 Troubleshooting

**Vector store not found:**
```bash
python scripts/setup_vectorstore.py
```

**Redis connection failed:**
```bash
docker run -d -p 6379:6379 --name afcon-redis redis:alpine
```

**Port 8000 already in use:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

**Groq API rate limit:**
- Free tier: 30 requests/minute
- Responses are cached to minimize API calls

## 🔐 Security Notes

- Never commit `.env` file
- Keep API keys secure
- Use HTTPS in production
- Implement rate limiting
- Restrict CORS origins

## 📈 Performance

- **Response Time**: < 500ms (cached), 1-3s (uncached)
- **Concurrent Users**: Supports 100+ with proper scaling
- **Memory Usage**: ~500MB with full vector store
- **Redis**: ~50MB for typical cache size

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## 📄 License

This project is for educational and demonstration purposes.

## 🙏 Acknowledgments

- ESPN API for match data
- Groq for LLM inference
- LangChain for RAG framework
- sentence-transformers for embeddings

---

**Last Updated**: January 4, 2026  
**Version**: 2.0 (with conversational memory)

## 📊 Data Pipeline

```
ESPN API → ETL Processor → CSV Files → Data Loader → Embeddings → FAISS Vector Store
                ↓                                                        ↓
         Live Data Module                                          RAG Module
                ↓                                                        ↓
                       → Query Dispatcher → Chatbot → Response
```

## 🔐 Environment Variables

Conf� Variables d'Environnement

Créer `.env` à la racine:
```env
GROQ_API_KEY=your_groq_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=true
```

## 📄 Licence

MIT License - Projet éducatif et démonstration