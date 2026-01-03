# AFCON Chatbot - Architecture Documentation

## System Overview

The AFCON Chatbot is a sophisticated AI-powered system that combines live data fetching, historical knowledge retrieval, and conversational AI to provide comprehensive information about the African Cup of Nations.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web UI     │  │   CLI Tool   │  │  REST API    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Server (Port 8000)                  │
│                    src/api/server.py                         │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   Chatbot Orchestrator                       │
│                   src/chatbot/chatbot.py                     │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Query Dispatcher (dispatcher.py)              │  │
│  │  Classifies: live | historical | statistics           │  │
│  └────────────────────┬──────────────────────────────────┘  │
└────────────────────────┼────────────────────────────────────┘
                         ↓
        ┌────────────────┴────────────────┐
        ↓                                  ↓
┌──────────────────┐            ┌──────────────────────┐
│  Live Data Path  │            │    RAG Data Path     │
└──────────────────┘            └──────────────────────┘
        ↓                                  ↓
┌──────────────────┐            ┌──────────────────────┐
│   ESPN API       │            │  Vector Store        │
│   src/live_data/ │            │  src/rag/            │
│                  │            │  src/knowledge_base/ │
│ • api_client.py  │            │                      │
│ • etl.py         │            │ • retriever.py       │
│ • live_store.py  │            │ • rag_chain.py       │
└──────────────────┘            │ • vector_store.py    │
                                │ • data_loader.py     │
                                └──────────────────────┘
                                         ↓
                                ┌──────────────────┐
                                │  FAISS Vector DB │
                                │  data/vector_    │
                                │  store/          │
                                └──────────────────┘
                                         ↑
                                ┌──────────────────┐
                                │ OpenAI Embeddings│
                                │ text-embedding-  │
                                │ 3-small          │
                                └──────────────────┘
                                         ↑
                                ┌──────────────────┐
                                │ Historical Data  │
                                │ CSV Files        │
                                │ data/historical/ │
                                └──────────────────┘
```

## Component Details

### 1. User Interfaces Layer

#### Web UI (`frontend/index.html`)
- Modern, responsive chat interface
- Real-time message updates
- Typing indicators
- Error handling
- Connects to FastAPI backend via REST

#### CLI Tool (`scripts/run_cli.py`)
- Terminal-based interface
- Command support (clear, live, quit)
- Formatted output
- Conversation history

#### REST API
- Direct HTTP access
- JSON request/response
- Documented with OpenAPI/Swagger

### 2. API Server Layer

**File**: `src/api/server.py`

**Technology**: FastAPI + Uvicorn

**Endpoints**:
```
GET  /              - API info
GET  /health        - Health check
GET  /info          - Configuration info
POST /chat          - Main chat endpoint
POST /live/set      - Set live match
POST /match/summary - Get match details
POST /conversation/clear - Clear history
```

**Features**:
- CORS enabled for web access
- Pydantic models for validation
- Error handling and HTTP status codes
- Async/await support

### 3. Chatbot Orchestrator

**File**: `src/chatbot/chatbot.py`

**Class**: `AFCONChatbot`

**Responsibilities**:
- Initialize all subsystems
- Route queries based on type
- Manage conversation state
- Format responses
- Handle errors

**Flow**:
1. Receive user query
2. Classify query type (dispatcher)
3. Route to appropriate handler
4. Format response
5. Return to user

### 4. Query Dispatcher

**File**: `src/chatbot/dispatcher.py`

**Class**: `QueryDispatcher`

**Query Classification**:
- **Live**: Current/ongoing match data
- **Historical**: Past tournaments, winners
- **Statistics**: Team/player performance metrics
- **General**: Other AFCON questions

**Classification Methods**:
- Keyword matching
- Pattern recognition
- Team name extraction
- Context analysis

### 5. Live Data Module

#### API Client (`src/live_data/api_client.py`)
```python
class ESPNAPIClient:
    - fetch_match_summary(event_id)
    - fetch_scoreboard(date)
    - get_live_match_status(event_id)
    - get_match_events(event_id)
```

**ESPN API Endpoints**:
- Summary: `/summary?event={id}`
- Scoreboard: `/scoreboard?dates={date}`

#### ETL Processor (`src/live_data/etl.py`)
```python
class AFCONDataProcessor:
    - process_match_summary()
    - camel_to_snake() - naming convention
    - normalize_columns()
    - enforce_numeric()
    - add_analytical_features()
```

**Output DataFrames**:
- `fact_match` - Match metadata
- `fact_team_match` - Team statistics
- `fact_goals` - Goal events
- `dim_team` - Team dimension

#### Live Manager (`src/live_data/live_data_store.py`)
```python
class LiveMatchManager:
    - fetch_update() - Get latest data
    - monitor_live() - Continuous monitoring
    - _detect_new_goals()
    - _detect_new_cards()
```

### 6. Knowledge Base Module

#### Data Loader (`src/knowledge_base/data_loader.py`)
```python
class AFCONDataLoader:
    - load_csv_files()
    - create_documents_from_matches()
    - create_documents_from_teams()
    - create_documents_from_goals()
    - load_all_documents()
```

**Document Format**:
```python
Document(
    page_content="Team: Morocco | Score: 3 | Possession: 65%",
    metadata={
        "source": "fact_team_match.csv",
        "match_id": "732133",
        "type": "match"
    }
)
```

#### Vector Store (`src/knowledge_base/vector_store.py`)
```python
class VectorStoreManager:
    - create_vectorstore(documents)
    - save_vectorstore(name)
    - load_vectorstore(name)
    - similarity_search(query, k)
    - add_documents(documents)
    - get_retriever(k)
```

**Technology**: FAISS (Facebook AI Similarity Search)
- Efficient similarity search
- GPU acceleration support
- Persistent storage
- Incremental updates

### 7. RAG Module

#### Retriever (`src/rag/retriever.py`)
```python
class AFCONRetriever:
    - retrieve(query, k, filter_type)
    - retrieve_with_scores(query, k)
    - get_compressed_retriever(k)
    - format_retrieved_context(docs)
```

**Retrieval Process**:
1. Convert query to embedding
2. Similarity search in FAISS
3. Return top-k documents
4. Optional compression

#### RAG Chain (`src/rag/rag_chain.py`)
```python
class AFCONRAGChain:
    - answer_question(question, k)
    - answer_with_sources(question, k)

class AFCONConversationalRAG(AFCONRAGChain):
    - conversation_history[]
    - clear_history()
```

**Prompt Template**:
```
Context from AFCON database:
{context}

User Question: {question}

[Instructions...]

Answer:
```

**LLM**: GPT-4 Turbo
- Temperature: 0.7 (balanced creativity)
- Max tokens: Configurable
- Streaming: Optional

## Data Flow Diagrams

### Live Query Flow

```
User: "What's the current score?"
  ↓
FastAPI: POST /chat
  ↓
Chatbot: Receives query
  ↓
Dispatcher: Classifies as "live"
  ↓
LiveMatchManager: fetch_update()
  ↓
ESPNAPIClient: fetch_match_summary(event_id)
  ↓
ESPN API: Returns JSON
  ↓
Chatbot: Format response
  ↓
User: "Morocco 3 - 0 Comoros"
```

### Historical Query Flow

```
User: "Which team has most wins?"
  ↓
FastAPI: POST /chat
  ↓
Chatbot: Receives query
  ↓
Dispatcher: Classifies as "historical"
  ↓
RAGChain: answer_question()
  ↓
Retriever: retrieve(query, k=5)
  ↓
VectorStore: similarity_search()
  ↓
FAISS: Returns top-5 documents
  ↓
RAGChain: Formats context + prompt
  ↓
OpenAI GPT-4: Generates answer
  ↓
Chatbot: Format response
  ↓
User: "Egypt has won 7 AFCON titles..."
```

### Data Pipeline Flow

```
ESPN API
  ↓
ESPNAPIClient.fetch_match_summary()
  ↓
AFCONDataProcessor.process_match_summary()
  ↓
DataFrames (fact_match, fact_team_match, etc.)
  ↓
CSV Files (afcon_*_.csv)
  ↓
AFCONDataLoader.load_csv_files()
  ↓
LangChain Documents
  ↓
OpenAI Embeddings API
  ↓
Vector Embeddings (1536 dimensions)
  ↓
VectorStoreManager.create_vectorstore()
  ↓
FAISS Index
  ↓
Saved to disk (data/vector_store/)
```

## Technology Stack Deep Dive

### Backend Framework
- **FastAPI**: Modern, fast, async Python web framework
- **Uvicorn**: ASGI server for async Python
- **Pydantic**: Data validation using Python type hints

### AI/ML Stack
- **OpenAI GPT-4 Turbo**: Language generation
- **text-embedding-3-small**: Efficient embeddings (1536D)
- **LangChain**: RAG orchestration framework
- **FAISS**: Vector similarity search

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Requests**: HTTP client for API calls

### Storage
- **FAISS**: In-memory vector database
- **CSV**: Historical data storage
- **JSON**: API data format

## Configuration Management

**File**: `config.py`

**Environment Variables** (`.env`):
```ini
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small
ESPN_BASE_URL=https://site.web.api.espn.com/...
REFRESH_INTERVAL=30
DATABASE_URL=sqlite:///./data/afcon.db
VECTOR_STORE_PATH=./data/vector_store
PORT=8000
DEBUG=True
```

**Settings Class**:
```python
class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    # ... more settings
    
    class Config:
        env_file = ".env"
```

## Security Considerations

1. **API Key Protection**
   - Never commit `.env` to git
   - Use environment variables in production
   - Rotate keys regularly

2. **Input Validation**
   - Pydantic models validate all inputs
   - SQL injection prevention (if using SQL)
   - Rate limiting (recommended for production)

3. **CORS Configuration**
   - Currently allows all origins (development)
   - Restrict in production

4. **Error Handling**
   - Sensitive info not exposed in errors
   - Logging for debugging
   - User-friendly error messages

## Performance Optimization

1. **Vector Store**
   - Pre-computed embeddings
   - FAISS for efficient search
   - Batch processing for loading

2. **API Caching** (Future)
   - Redis for frequent queries
   - Cache live data (30s TTL)
   - Invalidation strategy

3. **Async Operations**
   - FastAPI async endpoints
   - Non-blocking I/O
   - Parallel processing where possible

4. **Resource Management**
   - Connection pooling
   - Memory-efficient data structures
   - Lazy loading

## Scalability Considerations

### Current Limitations
- Single-instance deployment
- In-memory vector store
- No load balancing
- Limited concurrent users

### Scaling Strategies

**Horizontal Scaling**:
- Deploy multiple API instances
- Load balancer (nginx, AWS ALB)
- Shared vector store (Pinecone, Weaviate)

**Vertical Scaling**:
- Increase server resources
- GPU acceleration for FAISS
- Faster storage (SSD, NVMe)

**Database Scaling**:
- Move to PostgreSQL
- Read replicas
- Sharding by tournament/year

**Caching Layer**:
- Redis for hot data
- CDN for static assets
- Query result caching

## Monitoring & Observability

**Recommended Tools**:
- **Logging**: Python logging, Loguru
- **Metrics**: Prometheus + Grafana
- **Tracing**: Jaeger, OpenTelemetry
- **Errors**: Sentry

**Key Metrics**:
- Request latency (p50, p95, p99)
- Throughput (requests/second)
- Error rates
- Vector search performance
- OpenAI API usage & costs

## Deployment Options

### Local Development
```bash
python -m src.api.server
```

### Docker
```dockerfile
FROM python:3.10-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0"]
```

### Cloud Platforms
- **AWS**: EC2, ECS, Lambda
- **Google Cloud**: Cloud Run, GKE
- **Azure**: App Service, Container Instances
- **Heroku**: Web dyno

## Future Enhancements

1. **Multi-language Support**
   - English, French, Arabic
   - i18n framework

2. **Advanced Analytics**
   - Predictive modeling
   - Interactive visualizations
   - Performance trends

3. **Real-time Notifications**
   - WebSocket support
   - Push notifications
   - Email alerts

4. **Mobile App**
   - React Native / Flutter
   - Native iOS/Android

5. **Social Features**
   - User accounts
   - Saved queries
   - Share results

6. **Enhanced RAG**
   - Multi-modal (images, videos)
   - Document summarization
   - Fact-checking
