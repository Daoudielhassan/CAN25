# AFCON Chatbot - Setup Guide

## 📋 Prerequisites

- Python 3.10 or higher
- OpenAI API key
- Internet connection for API calls

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Prepare Historical Data

Your existing CSV files will be automatically moved to the `data/historical/` directory during setup. Files like:
- `afcon_732133_fact_match.csv`
- `afcon_732133_fact_team_match.csv`
- `afcon_732133_fact_goals.csv`
- `afcon_732133_dim_team.csv`
- Any other AFCON-related CSV files

### 4. Initialize Vector Store

This step creates embeddings of your historical data:

```bash
python scripts/setup_vectorstore.py
```

This will:
- Load all CSV files from `data/historical/`
- Convert them to embeddings using OpenAI
- Store them in FAISS vector database
- Save to `data/vector_store/`

**Note**: This requires OpenAI API credits and may take a few minutes.

### 5. Start the API Server

```bash
python -m src.api.server
```

Or with custom host/port:
```bash
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 6. Use the Chatbot

#### Option A: Web Interface (Recommended)

Open `frontend/index.html` in your web browser. The interface will automatically connect to the API server.

#### Option B: CLI Interface

```bash
python scripts/run_cli.py
```

Commands:
- Type any question about AFCON
- `clear` - Clear conversation history
- `live <event_id>` - Monitor a specific match
- `quit` - Exit

#### Option C: API Directly

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who scored for Morocco vs Comoros?"}'
```

## 📊 Additional Tools

### Monitor Live Match

Track a live match with real-time updates:

```bash
python scripts/monitor_live_match.py 732133
```

Replace `732133` with the ESPN event ID for the match you want to monitor.

### Run ETL on Match Data

Extract and process match data:

```bash
python scripts/run_etl.py 732133
```

This will:
- Fetch match data from ESPN API
- Process and clean the data
- Save to CSV files (fact_match, fact_team_match, fact_goals, dim_team)

## 🔧 Configuration

Edit `config.py` or `.env` to customize:

- `OPENAI_MODEL` - GPT model to use (default: gpt-4-turbo-preview)
- `EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-small)
- `REFRESH_INTERVAL` - Seconds between live updates (default: 30)
- `PORT` - API server port (default: 8000)

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and status |
| `/health` | GET | Health check |
| `/chat` | POST | Chat with the bot |
| `/live/set` | POST | Set live match to monitor |
| `/match/summary` | POST | Get match summary |
| `/conversation/clear` | POST | Clear conversation history |
| `/info` | GET | API configuration info |

## 📝 Example Queries

### Live Match Queries
- "What's the current score?"
- "Who scored in the match?"
- "Show me live updates"

### Historical Queries
- "Which team has the most AFCON wins?"
- "Who scored for Morocco vs Comoros?"
- "What was Egypt's performance in 2019?"

### Statistics Queries
- "What was Morocco's possession percentage?"
- "How many shots on target did Senegal have?"
- "Compare passing accuracy between teams"

## 🐛 Troubleshooting

### Vector store not found
Run: `python scripts/setup_vectorstore.py`

### API connection error
1. Make sure the API server is running
2. Check `http://localhost:8000/health`
3. Verify port 8000 is not in use

### OpenAI API errors
1. Check your API key in `.env`
2. Verify you have credits in your OpenAI account
3. Check internet connection

### No data loaded
1. Ensure CSV files are in `data/historical/`
2. Check CSV file format matches expected structure
3. Review logs during vector store setup

## 📦 Project Structure

```
CAN25/
├── src/
│   ├── live_data/       # Live match data fetching
│   ├── knowledge_base/  # Historical data & vector store
│   ├── rag/            # RAG retrieval & chains
│   ├── chatbot/        # Chatbot orchestration
│   └── api/            # FastAPI server
├── data/
│   ├── historical/     # CSV historical data
│   └── vector_store/   # FAISS embeddings
├── frontend/           # Web interface
├── scripts/            # Utility scripts
├── requirements.txt    # Python dependencies
├── config.py          # Configuration
└── .env               # Environment variables
```

## 🔐 Security Notes

- Never commit `.env` file with API keys
- Keep OpenAI API key secure
- Use environment variables for production
- Consider rate limiting for public deployments

## 📈 Performance Tips

1. **Vector Store**: Pre-compute embeddings for faster queries
2. **Caching**: Implement Redis for frequent queries
3. **Batch Processing**: Process multiple matches at once
4. **API Rate Limits**: Respect ESPN and OpenAI rate limits

## 🤝 Support

For issues or questions:
1. Check this setup guide
2. Review error logs
3. Verify all prerequisites are met
4. Check API documentation at `/docs`
