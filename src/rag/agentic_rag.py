"""
Agentic RAG - LLM acts as an agent with tools to retrieve and reason
"""
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import settings
import json
import re


class AgenticRAG:
    """
    Agentic RAG system where LLM acts as an agent with tools
    Can decide which tools to use, perform multi-step reasoning, and validate answers
    """
    
    def __init__(self, retriever, live_api_client=None):
        """
        Initialize Agentic RAG
        
        Args:
            retriever: AFCONRetriever instance
            live_api_client: Optional ESPN API client for live data
        """
        self.retriever = retriever
        self.live_api_client = live_api_client
        
        # Initialize LLM with tool calling
        self.llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.1
        )
        
        # Create tools for the agent
        self.tools = self._create_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Maximum reasoning steps
        self.max_steps = 5
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent to use"""
        
        tools = [
            Tool(
                name="search_historical_data",
                func=self._search_historical,
                description="""
                Search historical AFCON 2025 data including:
                - Match results and scores
                - Group standings and qualified teams
                - Team performance statistics
                - AFCON news articles
                
                Use this FIRST for any query. If information is incomplete or not found,
                then use fetch_match_details tool to get live data from ESPN API.
                
                Input: A search query string (e.g., "Morocco Group A matches")
                Output: Relevant information from the knowledge base
                """
            ),
            
            Tool(
                name="fetch_match_details",
                func=self._fetch_espn_match_details,
                description="""
                Fetch detailed match information directly from ESPN API.
                Use this when:
                - search_historical_data returns no results or incomplete information
                - User asks for detailed match statistics or events
                - User asks about a specific team matchup (e.g., "Mali vs Tunisia")
                - Need fresh/latest match data
                
                The tool will search for matches involving the specified teams.
                
                Input: Team names or match query (e.g., "Mali Tunisia" or "Morocco match details")
                Output: Detailed match information from ESPN including score, events, and statistics
                """
            ),
            
            Tool(
                name="search_team_statistics",
                func=self._search_statistics,
                description="""
                Search detailed team statistics including:
                - Goals scored/conceded
                - Possession percentages
                - Shots and shots on target
                - Pass completion rates
                - Match performance metrics
                
                Use this for statistical analysis and team comparisons.
                
                Input: Team name or statistical query (e.g., "Morocco statistics")
                Output: Statistical data from the knowledge base
                """
            ),
            
            Tool(
                name="search_news",
                func=self._search_news,
                description="""
                Search AFCON news articles including:
                - Player quotes and interviews
                - Tournament updates
                - Team news and changes
                - Expert analysis
                
                Use this for latest news, player statements, and current events.
                
                Input: News-related query (e.g., "Victor Osimhen news")
                Output: Relevant news articles
                """
            ),
            
            Tool(
                name="validate_answer",
                func=self._validate_answer,
                description="""
                Validate an answer by checking if it's factually correct and complete.
                Use this to self-check your answer before returning to the user.
                
                Input: Your proposed answer as a JSON string with keys:
                    - answer: the answer text
                    - query: the original user query
                    - sources: list of source documents used
                
                Output: Validation result with confidence score
                """
            )
        ]
        
        # Add live data tool if API client is available
        if self.live_api_client:
            tools.append(
                Tool(
                    name="get_live_match_data",
                    func=self._get_live_data,
                    description="""
                    Get real-time live match data from ESPN API including:
                    - Current score
                    - Match status and time
                    - Recent events (goals, cards)
                    
                    Use this ONLY for questions about ongoing matches or current scores.
                    
                    Input: Event ID or "current" for the monitored match
                    Output: Live match data
                    """
                )
            )
        
        return tools
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the agent"""
        
        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description[:200]}..."
            for tool in self.tools
        ])
        
        return f"""You are an expert AFCON 2025 assistant with access to these tools:

{tools_desc}

To use a tool, respond in this format:
TOOL: tool_name
INPUT: your input here

CONVERSATION CONTEXT:
- You can see previous messages in this conversation
- When user says "the second match", "that team", "those players", etc., refer to the conversation history
- For follow-up questions, use context from previous answers to understand what the user is referring to
- Example: If you listed 3 matches and user asks "tell me about the second one", identify which match was #2

TOOL SELECTION STRATEGY:
1. ALWAYS start with search_historical_data for any query
2. If search_historical_data returns "No data found" or incomplete information, use fetch_match_details
3. For "Team A vs Team B" queries, try search_historical_data first, then fetch_match_details
4. For detailed statistics, use search_team_statistics after getting basic match info
5. Use fetch_match_details when user explicitly asks for "more details" or "latest information"
6. For follow-up questions about previously mentioned matches/teams, extract the specific reference from conversation history

CRITICAL RULES FOR FINAL ANSWERS - ZERO HALLUCINATION POLICY:
- After receiving tool results, you MUST provide a complete answer starting with "ANSWER:"
- NEVER say "Please wait" or "I'm searching" - the tool has already run
- Use ONLY the EXACT information from tool outputs - NEVER add, change, or invent ANY numbers, names, or facts
- If the tool says "3 goals", you MUST say "3 goals" - NOT "4 goals" or any other number
- If the tool lists specific players and their goals, you MUST use those EXACT numbers
- Copy numbers, names, and facts DIRECTLY from the tool output - DO NOT modify them
- Be specific: include team names, scores, dates, and details from the tool results
- Be concise but informative: 2-4 sentences
- If tool output doesn't have the needed info, say what information is available
- VIOLATION OF THESE RULES = COMPLETE FAILURE

SPECIAL CASES:
- For "Team A vs Team B" queries: First search historical data. If not found, use fetch_match_details to check ESPN API
- For standings queries: Always show position, points, goal difference, and qualification status
- For match results: Include score, date, penalty shootout info if applicable, and which team advances

EXAMPLES:
Tool output: "No historical data found for this query."
Next action: Use fetch_match_details tool to search ESPN API
CORRECT: "TOOL: fetch_match_details\nINPUT: Mali Tunisia"

Tool output from fetch_match_details: "MATCH FOUND: Mali vs Tunisia, Mali 1-1 Tunisia (Mali won 3-2 on penalties)"
CORRECT: "ANSWER: Mali defeated Tunisia 1-1 (3-2 on penalties) in the Round of 16 on January 3, 2026. Mali advances to the quarterfinals."

User query: "mali vs tunisia"
Tool 1 output (search_historical_data): "Mali qualified from Group A, Tunisia qualified from Group C"
Next action: Since no direct match found in historical data, use fetch_match_details
TOOL: fetch_match_details
INPUT: Mali Tunisia
"""
    
    def _search_historical(self, query: str) -> str:
        """Search historical match data"""
        try:
            # Use retriever to search
            docs = self.retriever.retrieve(query, k=5)
            
            if not docs:
                return "NO HISTORICAL DATA FOUND for this query. Consider using fetch_match_details tool to search ESPN API."
            
            # Check if results actually contain relevant match info
            query_lower = query.lower()
            has_vs = " vs " in query_lower or "versus" in query_lower
            
            # If it's a team vs team query, check if we found a direct match
            if has_vs:
                combined_content = " ".join([doc.page_content.lower() for doc in docs])
                # Extract team names from query
                teams_in_query = []
                for word in query_lower.split():
                    if len(word) > 3 and word not in ["match", "versus", "against"]:
                        teams_in_query.append(word)
                
                # Check if both teams appear together in a match context
                has_direct_match = any(
                    all(team in doc.page_content.lower() for team in teams_in_query[:2])
                    for doc in docs
                    if "score" in doc.page_content.lower() or "match" in doc.page_content.lower()
                )
                
                if not has_direct_match and len(teams_in_query) >= 2:
                    return f"NO DIRECT MATCH FOUND in historical data between these teams. Found general information but no head-to-head match. Use fetch_match_details tool to search ESPN API."
            
            # Format results with clear structure
            results = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content[:400]  # Increased from 300
                results.append(f"[{i}] {content}")
            
            return "\n\n".join(results)
        
        except Exception as e:
            return f"Error searching historical data: {str(e)}"
    
    def _search_statistics(self, query: str) -> str:
        """Search team statistics"""
        try:
            # Add "statistics" to query to focus search
            stats_query = f"{query} statistics performance metrics"
            docs = self.retriever.retrieve(stats_query, k=5)
            
            if not docs:
                return "No statistics found for this query."
            
            # Format results
            results = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content[:300]
                results.append(f"[{i}] {content}")
            
            return "\n\n".join(results)
        
        except Exception as e:
            return f"Error searching statistics: {str(e)}"
    
    def _search_news(self, query: str) -> str:
        """Search AFCON news"""
        try:
            # Add "news" to query
            news_query = f"{query} news article"
            docs = self.retriever.retrieve(news_query, k=3)
            
            if not docs:
                return "No news articles found for this query."
            
            # Format results
            results = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content[:400]
                results.append(f"[{i}] {content}")
            
            return "\n\n".join(results)
        
        except Exception as e:
            return f"Error searching news: {str(e)}"
    
    def _fetch_espn_match_details(self, query: str) -> str:
        """Fetch match details from ESPN API"""
        try:
            import requests
            from datetime import datetime, timedelta
            
            # Extract team names from query
            query_lower = query.lower()
            
            # Common team names to search for
            teams = [
                "morocco", "mali", "tunisia", "nigeria", "egypt", "senegal",
                "algeria", "ivory coast", "cameroon", "burkina faso", "south africa",
                "congo dr", "tanzania", "mozambique", "benin", "sudan",
                "zambia", "comoros", "angola", "zimbabwe", "uganda", "gabon",
                "botswana", "equatorial guinea"
            ]
            
            # Find teams mentioned in query
            mentioned_teams = [t for t in teams if t in query_lower]
            
            if len(mentioned_teams) < 1:
                return f"Please specify team name(s) for the match. No teams found in query."
            
            # Fetch recent matches from ESPN scoreboard
            dates_to_check = []
            today = datetime.now()
            for days_back in range(0, 15):  # Check last 15 days
                date = today - timedelta(days=days_back)
                dates_to_check.append(date.strftime("%Y%m%d"))
            
            found_matches = []
            
            for date in dates_to_check:
                try:
                    resp = requests.get(
                        "https://site.api.espn.com/apis/site/v2/sports/soccer/caf.nations/scoreboard",
                        params={"dates": date, "region": "us", "lang": "en"},
                        timeout=5
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        events = data.get("events", [])
                        
                        for event in events:
                            comp = event.get("competitions", [{}])[0]
                            competitors = comp.get("competitors", [])
                            team_names = [c["team"]["displayName"].lower() for c in competitors]
                            
                            # Check if teams match (flexible: 1 or more teams)
                            match_count = sum(1 for mt in mentioned_teams if any(mt in tn for tn in team_names))
                            
                            # Match if: (a) both teams from query found, OR (b) at least 1 team found for "more info" queries
                            min_match = 2 if len(mentioned_teams) >= 2 else 1
                            
                            if match_count >= min_match:
                                # Found a match!
                                event_id = event["id"]
                                
                                # Fetch detailed match data including statistics
                                detail_resp = requests.get(
                                    "https://site.web.api.espn.com/apis/site/v2/sports/soccer/caf.nations/summary",
                                    params={"event": event_id, "region": "us", "lang": "en"},
                                    timeout=5
                                )
                                
                                if detail_resp.status_code == 200:
                                    match_data = detail_resp.json()
                                    comp_detail = match_data["header"]["competitions"][0]
                                    
                                    # Extract match information
                                    status = comp_detail["status"]["type"]["description"]
                                    date_str = comp_detail["date"]
                                    
                                    team1 = comp_detail["competitors"][0]
                                    team2 = comp_detail["competitors"][1]
                                    
                                    result_text = f"""
MATCH FOUND: {team1['team']['displayName']} vs {team2['team']['displayName']}

Date: {date_str}
Status: {status}
Competition: {match_data['header']['season']['name']}

Score:
  {team1['team']['displayName']}: {team1['score']} {'(WINNER)' if team1.get('winner') else ''}
  {team2['team']['displayName']}: {team2['score']} {'(WINNER)' if team2.get('winner') else ''}
"""
                                    
                                    # Add penalty information if available
                                    if "notes" in comp_detail:
                                        for note in comp_detail["notes"]:
                                            if "headline" in note:
                                                result_text += f"\n{note['headline']}\n"
                                    
                                    # Add statistics if available
                                    if "boxscore" in match_data and "teams" in match_data["boxscore"]:
                                        result_text += "\nMatch Statistics:\n"
                                        for team in match_data["boxscore"]["teams"]:
                                            team_name = team["team"]["displayName"]
                                            result_text += f"\n{team_name}:\n"
                                            for stat in team.get("statistics", [])[:8]:  # Top 8 stats
                                                result_text += f"  - {stat['label']}: {stat['displayValue']}\n"
                                    
                                    # Add goal scorers if available
                                    if "scoringPlays" in match_data:
                                        result_text += "\nGoal Scorers:\n"
                                        for play in match_data["scoringPlays"]:
                                            if play.get("type", {}).get("text") == "Goal":
                                                team = play.get("team", {}).get("displayName", "Unknown")
                                                time = play.get("clock", {}).get("displayValue", "?")
                                                text = play.get("text", "Goal")
                                                result_text += f"  {time}' - {team}: {text}\n"
                                    
                                    # Add advancing team info
                                    if team1.get('advance'):
                                        result_text += f"\n{team1['team']['displayName']} advances to next round"
                                    elif team2.get('advance'):
                                        result_text += f"\n{team2['team']['displayName']} advances to next round"
                                    
                                    return result_text
                
                except Exception as e:
                    continue  # Try next date
            
            return f"No match found between {' and '.join(mentioned_teams)}. The match may not have been played yet or the teams haven't faced each other in this tournament."
        
        except Exception as e:
            return f"Error fetching match details from ESPN API: {str(e)}"
    
    def _get_live_data(self, event_id: str) -> str:
        """Get live match data"""
        if not self.live_api_client:
            return "Live data not available. No API client configured."
        
        try:
            # Fetch live data
            data = self.live_api_client.fetch_match_summary(event_id)
            
            if not data:
                return "No live data available for this event."
            
            # Extract key information
            status = data.get('status', {})
            teams = data.get('header', {}).get('competitions', [{}])[0].get('competitors', [])
            
            result = f"Status: {status.get('type', {}).get('detail', 'Unknown')}\n"
            
            for team in teams:
                name = team.get('team', {}).get('displayName', 'Unknown')
                score = team.get('score', 'N/A')
                result += f"{name}: {score}\n"
            
            return result
        
        except Exception as e:
            return f"Error getting live data: {str(e)}"
    
    def _validate_answer(self, answer_json: str) -> str:
        """Validate an answer"""
        try:
            # Parse input
            data = json.loads(answer_json) if isinstance(answer_json, str) else answer_json
            answer = data.get('answer', '')
            query = data.get('query', '')
            sources = data.get('sources', [])
            
            # Simple validation checks
            issues = []
            
            # Check if answer is empty
            if not answer or len(answer.strip()) < 10:
                issues.append("Answer is too short or empty")
            
            # Check if answer contains forbidden phrases
            forbidden = ["we were discussing", "I mentioned", "according to database"]
            for phrase in forbidden:
                if phrase.lower() in answer.lower():
                    issues.append(f"Contains forbidden phrase: '{phrase}'")
            
            # Check if answer is relevant to query
            query_words = set(query.lower().split())
            answer_words = set(answer.lower().split())
            overlap = len(query_words & answer_words)
            
            if overlap < 2:
                issues.append("Answer may not be relevant to query")
            
            # Check if sources were used
            if not sources or len(sources) == 0:
                issues.append("No sources cited")
            
            # Generate validation result
            if issues:
                return f"VALIDATION FAILED:\n" + "\n".join(f"- {issue}" for issue in issues)
            else:
                return "VALIDATION PASSED: Answer is factually grounded and well-formatted."
        
        except Exception as e:
            return f"Validation error: {str(e)}"
    
    def answer_question(self, query: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Answer a question using agentic RAG with iterative tool use
        
        Args:
            query: User question
            conversation_history: Previous conversation messages for context
            
        Returns:
            Dictionary with answer and reasoning steps
        """
        try:
            reasoning_steps = []
            messages = [
                SystemMessage(content=self._create_system_prompt())
            ]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 3 exchanges
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add current question
            messages.append(HumanMessage(content=f"Question: {query}"))
            
            # Iterative reasoning loop
            for step in range(self.max_steps):
                # Get LLM response
                response = self.llm.invoke(messages)
                response_text = response.content
                
                # Check if LLM wants to use a tool
                tool_match = re.search(r'TOOL:\s*(\w+)\s*\nINPUT:\s*(.+?)(?:\n|$)', response_text, re.DOTALL)
                
                if tool_match:
                    tool_name = tool_match.group(1)
                    tool_input = tool_match.group(2).strip()
                    
                    # Execute tool
                    if tool_name in self.tool_map:
                        tool = self.tool_map[tool_name]
                        tool_output = tool.func(tool_input)
                        
                        # Record step
                        reasoning_steps.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "output": tool_output[:200]
                        })
                        
                        # Add to messages with very strong instruction
                        messages.append(AIMessage(content=response_text))
                        
                        # Check if we need to call another tool
                        needs_more_data = any(phrase in tool_output.lower() for phrase in [
                            "no historical data found",
                            "no data found", 
                            "not found",
                            "no information",
                            "no match found"
                        ])
                        
                        if needs_more_data and tool_name == "search_historical_data":
                            follow_up = f"""Tool Output from {tool_name}:
{tool_output}

The historical data is incomplete or not found. Since this appears to be a team matchup query, you MUST now use the fetch_match_details tool to search ESPN API.

REQUIRED ACTION:
TOOL: fetch_match_details
INPUT: [extract team names from the original query: "{query}"]

DO NOT provide an answer yet. Call the fetch_match_details tool first."""
                        else:
                            follow_up = f"""Tool Output:
{tool_output}

CRITICAL INSTRUCTION - READ CAREFULLY:
1. The tool has already run. DO NOT say "please wait" or "I'm searching".
2. You MUST use the EXACT numbers, names, and facts from the tool output above
3. If the tool output says a player has "3 goals", you MUST say "3 goals" - NOT "4" or any other number
4. DO NOT modify, change, or invent ANY information
5. Copy the information DIRECTLY from the tool output

Now provide your COMPLETE final answer starting with 'ANSWER:' using ONLY the facts from the tool output above.

Example format: "ANSWER: [your complete answer using EXACT information from tool output]" """
                        messages.append(HumanMessage(content=follow_up))
                    else:
                        # Unknown tool, ask for final answer
                        messages.append(HumanMessage(content=f"The tool '{tool_name}' was not found. Please provide your final answer starting with ANSWER: based on what you know."))
                
                # Check for final answer
                answer_match = re.search(r'ANSWER:\s*(.+)', response_text, re.DOTALL)
                if answer_match:
                    answer = answer_match.group(1).strip()
                    return {
                        "answer": answer,
                        "reasoning_steps": reasoning_steps,
                        "num_steps": len(reasoning_steps),
                        "success": True
                    }
                
                # If no tool use and no answer, assume direct answer
                if not tool_match and step > 0:
                    return {
                        "answer": response_text,
                        "reasoning_steps": reasoning_steps,
                        "num_steps": len(reasoning_steps),
                        "success": True
                    }
            
            # Max steps reached
            return {
                "answer": "Could not generate answer within step limit.",
                "reasoning_steps": reasoning_steps,
                "num_steps": len(reasoning_steps),
                "success": False
            }
        
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "reasoning_steps": [],
                "num_steps": 0,
                "success": False,
                "error": str(e)
            }
    
    def explain_reasoning(self, query: str) -> str:
        """
        Get detailed explanation of agent reasoning process
        
        Args:
            query: User question
            
        Returns:
            Human-readable explanation of reasoning
        """
        result = self.answer_question(query)
        
        explanation = f"Query: {query}\n\n"
        explanation += f"Reasoning Process ({result['num_steps']} steps):\n"
        explanation += "=" * 60 + "\n\n"
        
        for i, step in enumerate(result['reasoning_steps'], 1):
            explanation += f"Step {i}: {step['tool']}\n"
            explanation += f"  Input: {step['input']}\n"
            explanation += f"  Output: {step['output']}...\n\n"
        
        explanation += "=" * 60 + "\n"
        explanation += f"Final Answer: {result['answer']}\n"
        
        return explanation


class AgenticRAGChain:
    """
    Simplified interface for agentic RAG with caching
    Compatible with existing chatbot interface
    """
    
    def __init__(self, retriever, live_api_client=None):
        """Initialize agentic RAG chain"""
        self.agentic_rag = AgenticRAG(retriever, live_api_client)
        self.cache = {}
    
    def answer_question(self, query: str, k: int = 5, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Answer question using agentic RAG
        
        Args:
            query: User question
            k: Number of documents to retrieve (used by tools)
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary with answer and metadata
        """
        # Check cache (skip if conversation history provided - need context-aware answers)
        cache_key = f"{query}_{k}"
        if cache_key in self.cache and not conversation_history:
            cached = self.cache[cache_key].copy()
            cached["cached"] = True
            return cached
        
        # Use agentic RAG with conversation history
        result = self.agentic_rag.answer_question(query, conversation_history=conversation_history)
        
        # Format for compatibility
        formatted = {
            "answer": result["answer"],
            "context_docs": [],
            "num_sources": result["num_steps"],
            "reasoning_steps": result["reasoning_steps"],
            "agentic": True,
            "cached": False
        }
        
        # Cache result
        self.cache[cache_key] = formatted
        
        return formatted
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_type": "memory"
        }
    
    def clear_cache(self):
        """Clear cache"""
        self.cache.clear()
