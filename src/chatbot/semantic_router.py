"""
Semantic routing using embeddings for query classification
Routes queries based on semantic similarity rather than keyword matching
"""
import numpy as np
from typing import Dict, Any, List, Literal
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
from config import settings


QueryType = Literal["live_data", "static_knowledge", "statistics", "general"]


class SemanticRouter:
    """
    Lightweight semantic router using embeddings to classify queries
    Determines whether to use RAG (static knowledge) or API calls (dynamic data)
    """
    
    def __init__(self):
        """Initialize semantic router with embedding model and example clusters"""
        # Use sentence-transformers model for embeddings
        # Don't use settings.embedding_model as it's set to Gemini's model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Define example queries for each cluster
        self.query_clusters = {
            "live_data": [
                "What is the current score?",
                "Is there a match happening now?",
                "What's the live score of the game?",
                "Show me the ongoing match",
                "What's happening in the match right now?",
                "Current match status",
                "Real-time score updates",
                "Live match information",
                "What's the score at the moment?",
                "Who's winning right now?"
            ],
            "static_knowledge": [
                "Which teams qualified from Group A?",
                "What was the final score of Morocco vs Comoros?",
                "Who won the match between Mali and Zambia?",
                "Show me Morocco's group stage matches",
                "What are the group standings?",
                "Which teams advanced to knockout stage?",
                "Historical match results",
                "Past tournament winners",
                "Team performance in previous matches",
                "Match summary between two teams",
                "What is the AFCON news?",
                "Latest headlines about the tournament",
                "Tell me about Victor Osimhen",
                "Who are the best players?"
            ],
            "statistics": [
                "What are the team statistics?",
                "Show me possession stats",
                "How many shots did Morocco have?",
                "Compare team performances",
                "Player statistics for the match",
                "Total goals scored by team",
                "Shot accuracy percentage",
                "Pass completion rate",
                "Average goals per match",
                "Team performance metrics"
            ],
            "general": [
                "Hello",
                "What can you do?",
                "Help me understand",
                "Tell me about AFCON",
                "What is this chatbot for?",
                "How does this work?",
                "What information do you have?",
                "Can you help me?"
            ]
        }
        
        # Pre-compute embeddings for all cluster examples
        self.cluster_embeddings = self._compute_cluster_embeddings()
        
        # Similarity threshold for confident routing
        self.confidence_threshold = 0.65
    
    def _compute_cluster_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Pre-compute embeddings for all example queries in each cluster
        
        Returns:
            Dictionary mapping cluster names to their embedding matrices
        """
        cluster_embeddings = {}
        
        for cluster_name, examples in self.query_clusters.items():
            # Embed all examples for this cluster
            embeddings = self.embeddings.embed_documents(examples)
            cluster_embeddings[cluster_name] = np.array(embeddings)
        
        return cluster_embeddings
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify query using semantic similarity to example clusters
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with classification results including:
            - query_type: The predicted cluster
            - confidence: Similarity score (0-1)
            - use_rag: Whether to use RAG system
            - use_live_api: Whether to call live data API
            - routing_decision: Human-readable explanation
        """
        # Embed the user query
        query_embedding = np.array(self.embeddings.embed_query(query)).reshape(1, -1)
        
        # Calculate similarity to each cluster
        cluster_scores = {}
        
        for cluster_name, cluster_embs in self.cluster_embeddings.items():
            # Compute cosine similarity to all examples in cluster
            similarities = cosine_similarity(query_embedding, cluster_embs)[0]
            
            # Use max similarity as cluster score
            cluster_scores[cluster_name] = float(np.max(similarities))
        
        # Find best matching cluster
        best_cluster = max(cluster_scores, key=cluster_scores.get)
        confidence = cluster_scores[best_cluster]
        
        # Determine routing based on cluster
        use_rag = best_cluster in ["static_knowledge", "statistics"]
        use_live_api = best_cluster == "live_data"
        
        # If confidence is low, default to RAG (safer choice)
        if confidence < self.confidence_threshold:
            best_cluster = "static_knowledge"
            use_rag = True
            use_live_api = False
            routing_decision = f"Low confidence ({confidence:.2f}), defaulting to RAG"
        else:
            routing_decision = f"Confident match ({confidence:.2f}) to {best_cluster}"
        
        return {
            "query_type": best_cluster,
            "confidence": confidence,
            "use_rag": use_rag,
            "use_live_api": use_live_api,
            "cluster_scores": cluster_scores,
            "routing_decision": routing_decision,
            "original_query": query
        }
    
    def route(self, query: str) -> str:
        """
        Simple routing method that returns the target handler
        
        Args:
            query: User query
            
        Returns:
            Handler name: 'rag' or 'live_api' or 'general'
        """
        classification = self.classify_query(query)
        
        if classification["use_live_api"]:
            return "live_api"
        elif classification["use_rag"]:
            return "rag"
        else:
            return "general"
    
    def add_examples(self, cluster_name: str, examples: List[str]) -> None:
        """
        Add new example queries to a cluster (useful for fine-tuning)
        
        Args:
            cluster_name: Name of the cluster
            examples: List of example queries to add
        """
        if cluster_name not in self.query_clusters:
            self.query_clusters[cluster_name] = []
        
        self.query_clusters[cluster_name].extend(examples)
        
        # Re-compute embeddings for this cluster
        all_examples = self.query_clusters[cluster_name]
        embeddings = self.embeddings.embed_documents(all_examples)
        self.cluster_embeddings[cluster_name] = np.array(embeddings)
    
    def explain_routing(self, query: str) -> str:
        """
        Provide detailed explanation of routing decision
        
        Args:
            query: User query
            
        Returns:
            Human-readable explanation
        """
        result = self.classify_query(query)
        
        explanation = f"Query: '{query}'\n\n"
        explanation += f"Routing Decision: {result['routing_decision']}\n\n"
        explanation += "Similarity Scores:\n"
        
        for cluster, score in sorted(result['cluster_scores'].items(), 
                                    key=lambda x: x[1], 
                                    reverse=True):
            explanation += f"  - {cluster}: {score:.3f}\n"
        
        explanation += f"\nFinal Routing:\n"
        explanation += f"  - Use RAG: {result['use_rag']}\n"
        explanation += f"  - Use Live API: {result['use_live_api']}\n"
        
        return explanation


if __name__ == "__main__":
    """Test the semantic router"""
    
    router = SemanticRouter()
    
    # Test queries
    test_queries = [
        "Which teams qualified from Group A?",
        "What's the current score?",
        "Show me Morocco's statistics",
        "Is there a live match now?",
        "What was the result of Mali vs Zambia?",
        "Hello, what can you do?",
        "Latest AFCON news",
        "Real-time match updates"
    ]
    
    print("[ROUTER] Semantic Router Test\n")
    print("=" * 60)
    
    for query in test_queries:
        result = router.classify_query(query)
        handler = router.route(query)
        
        print(f"\n[NOTE] Query: {query}")
        print(f"   Type: {result['query_type']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Handler: {handler}")
        print(f"   Decision: {result['routing_decision']}")
