# enhanced_rag_integration.py - Integration module for enhanced RAG
"""
Integration module that enhances the existing RAG system with FAISS vectorstore
"""

import os
import json
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    ENHANCED_RAG_AVAILABLE = True
except ImportError:
    logger.warning("Enhanced RAG components not available")
    ENHANCED_RAG_AVAILABLE = False


class EnhancedRAGIntegration:
    """Enhanced RAG integration for the FVI system"""
    
    def __init__(self, vectorstore_dir: str = "vectorstore"):
        self.vectorstore_dir = Path(vectorstore_dir)
        self.embedding_model = None
        self.faiss_index = None
        self.metadata = []
        self.index_info = {}
        self.available = False
        
        if ENHANCED_RAG_AVAILABLE:
            self._initialize()
    
    def _initialize(self):
        """Initialize the enhanced RAG system"""
        try:
            # Check if required files exist
            required_files = ["index.faiss", "metadata.pkl", "index.json"]
            for file_name in required_files:
                if not (self.vectorstore_dir / file_name).exists():
                    logger.warning(f"Required file missing: {file_name}")
                    return
            
            # Load index info
            with open(self.vectorstore_dir / "index.json", 'r') as f:
                self.index_info = json.load(f)
            
            # Load embedding model
            model_name = self.index_info.get("embedding_model", "all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer(model_name)
            
            # Load FAISS index
            self.faiss_index = faiss.read_index(str(self.vectorstore_dir / "index.faiss"))
            
            # Load metadata
            with open(self.vectorstore_dir / "metadata.pkl", 'rb') as f:
                self.metadata = pickle.load(f)
            
            self.available = True
            logger.info(f"Enhanced RAG initialized with {len(self.metadata)} documents")
            
        except Exception as e:
            logger.error(f"Enhanced RAG initialization failed: {e}")
            self.available = False
    
    def search_relevant_documents(self, query: str, top_k: int = 5, score_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search for relevant documents using FAISS"""
        if not self.available:
            return []
        
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode([query])
            query_normalized = query_embedding / np.linalg.norm(query_embedding)
            
            # Search FAISS index
            scores, indices = self.faiss_index.search(
                query_normalized.astype(np.float32), 
                min(top_k, len(self.metadata))
            )
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= score_threshold and idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result['relevance_score'] = float(score)
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_context_for_country(self, country: str, query: str = "", top_k: int = 3) -> str:
        """Get context specific to a country"""
        if not self.available:
            return f"Enhanced context not available for {country}"
        
        try:
            # Search for country-specific content
            country_query = f"{country} coal industry assessment {query}".strip()
            results = self.search_relevant_documents(country_query, top_k=top_k * 2)
            
            # Filter for country-specific results
            country_results = []
            for result in results:
                content = result.get('content', '').lower()
                if country.lower() in content or result.get('country', '').lower() == country.lower():
                    country_results.append(result)
            
            # Take top results
            final_results = country_results[:top_k] if country_results else results[:top_k]
            
            # Format context
            context_parts = []
            for result in final_results:
                if 'content' in result:
                    context_parts.append(result['content'])
                elif result.get('type') == 'country_scores':
                    scores = result.get('scores', {})
                    score_text = f"{country} Assessment - "
                    score_text += f"Overall: {result.get('overall_score', 'N/A')}, "
                    score_text += f"Key dimensions: Infrastructure({scores.get('infrastructure', 'N/A')}), "
                    score_text += f"Economic({scores.get('economic', 'N/A')}), "
                    score_text += f"Emissions({scores.get('emissions', 'N/A')})"
                    context_parts.append(score_text)
            
            return "\n\n".join(context_parts) if context_parts else f"Limited enhanced context for {country}"
            
        except Exception as e:
            logger.error(f"Failed to get country context: {e}")
            return f"Error retrieving enhanced context for {country}"
    
    def enhance_query_response(self, query: str, country: str = None, persona: str = "analyst") -> Dict[str, Any]:
        """Enhance a query response with vectorstore context"""
        if not self.available:
            return {"enhanced": False, "reason": "Enhanced RAG not available"}
        
        try:
            # Get relevant documents
            results = self.search_relevant_documents(query, top_k=8)
            
            # Get country-specific context if provided
            country_context = ""
            if country:
                country_context = self.get_context_for_country(country, query, top_k=3)
            
            # Organize and structure the context
            structured_context = self._structure_context(results, query, country, persona)
            
            enhanced_context = {
                "structured_context": structured_context,
                "country_context": country_context,
                "relevant_documents": len(results),
                "persona": persona,
                "enhanced": True,
                "context_categories": structured_context.get("categories", []),
                "key_insights": structured_context.get("key_insights", []),
                "data_sources": structured_context.get("data_sources", [])
            }
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Failed to enhance query response: {e}")
            return {"enhanced": False, "reason": f"Error: {e}"}
    
    def _structure_context(self, results: List[Dict], query: str, country: str = None, persona: str = "analyst") -> Dict[str, Any]:
        """Structure the retrieved context into organized categories"""
        try:
            # Initialize categories
            context_categories = {
                "industry_overview": [],
                "technical_data": [],
                "economic_factors": [],
                "environmental_impact": [],
                "policy_regulatory": [],
                "market_trends": [],
                "country_specific": []
            }
            
            key_insights = []
            data_sources = set()
            
            # Categorize content based on keywords and context
            for result in results:
                content = result.get('content', '')
                source = result.get('source', 'Knowledge Base')
                relevance = result.get('relevance_score', 0)
                
                if len(content) < 50:
                    continue
                
                data_sources.add(source)
                
                # Categorize based on content keywords
                content_lower = content.lower()
                
                # Industry Overview
                if any(keyword in content_lower for keyword in ['coal industry', 'mining', 'production capacity', 'global', 'overview']):
                    context_categories["industry_overview"].append({
                        "content": content,
                        "relevance": relevance,
                        "source": source
                    })
                
                # Technical Data
                elif any(keyword in content_lower for keyword in ['energy content', 'btu', 'quality', 'grade', 'reserves', 'specifications']):
                    context_categories["technical_data"].append({
                        "content": content,
                        "relevance": relevance,
                        "source": source
                    })
                
                # Economic Factors
                elif any(keyword in content_lower for keyword in ['price', 'cost', 'economic', 'market', 'revenue', 'investment', 'financial']):
                    context_categories["economic_factors"].append({
                        "content": content,
                        "relevance": relevance,
                        "source": source
                    })
                
                # Environmental Impact
                elif any(keyword in content_lower for keyword in ['emissions', 'carbon', 'co2', 'environmental', 'climate', 'pollution']):
                    context_categories["environmental_impact"].append({
                        "content": content,
                        "relevance": relevance,
                        "source": source
                    })
                
                # Policy & Regulatory
                elif any(keyword in content_lower for keyword in ['policy', 'regulation', 'government', 'subsidy', 'tax', 'legal', 'compliance']):
                    context_categories["policy_regulatory"].append({
                        "content": content,
                        "relevance": relevance,
                        "source": source
                    })
                
                # Market Trends
                elif any(keyword in content_lower for keyword in ['trend', 'future', 'outlook', 'forecast', 'growth', 'decline', 'transition']):
                    context_categories["market_trends"].append({
                        "content": content,
                        "relevance": relevance,
                        "source": source
                    })
                
                # Country-specific (if country mentioned)
                elif country and country.lower() in content_lower:
                    context_categories["country_specific"].append({
                        "content": content,
                        "relevance": relevance,
                        "source": source
                    })
                
                # Extract key insights (high relevance items)
                if relevance > 0.7:
                    insight = self._extract_key_insight(content, query)
                    if insight:
                        key_insights.append(insight)
            
            # Sort categories by relevance
            for category in context_categories:
                context_categories[category] = sorted(
                    context_categories[category], 
                    key=lambda x: x['relevance'], 
                    reverse=True
                )[:3]  # Keep top 3 per category
            
            # Filter out empty categories
            active_categories = {k: v for k, v in context_categories.items() if v}
            
            return {
                "categories": active_categories,
                "key_insights": key_insights[:5],  # Top 5 insights
                "data_sources": list(data_sources),
                "total_relevant_items": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error structuring context: {e}")
            return {"categories": {}, "key_insights": [], "data_sources": [], "total_relevant_items": 0}
    
    def _extract_key_insight(self, content: str, query: str) -> str:
        """Extract a key insight from content"""
        try:
            # Split content into sentences
            sentences = content.split('.')
            query_words = query.lower().split()
            
            # Find sentences that contain query terms
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and any(word in sentence.lower() for word in query_words):
                    # Clean and format the insight
                    if sentence and not sentence.endswith('.'):
                        sentence += '.'
                    return sentence
            
            # Fallback: return first substantial sentence
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 30:
                    if sentence and not sentence.endswith('.'):
                        sentence += '.'
                    return sentence
                    
            return None
            
        except Exception:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get enhanced RAG statistics"""
        if not self.available:
            return {"available": False}
        
        return {
            "available": True,
            "total_documents": len(self.metadata),
            "embedding_model": self.index_info.get("embedding_model"),
            "dimension": self.index_info.get("dimension"),
            "knowledge_chunks": len([m for m in self.metadata if m.get('type') == 'knowledge']),
            "country_assessments": len([m for m in self.metadata if m.get('type') == 'country_scores']),
            "created_at": self.index_info.get("created_at")
        }


# Global instance for easy access
enhanced_rag = EnhancedRAGIntegration()


def get_enhanced_context(query: str, country: str = None, persona: str = "analyst") -> Dict[str, Any]:
    """Get enhanced context for a query (convenience function)"""
    return enhanced_rag.enhance_query_response(query, country, persona)


def search_fvi_knowledge(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search FVI knowledge base (convenience function)"""
    return enhanced_rag.search_relevant_documents(query, top_k)


def is_enhanced_rag_available() -> bool:
    """Check if enhanced RAG is available"""
    return enhanced_rag.available


if __name__ == "__main__":
    # Test the enhanced RAG integration
    print("🔧 Testing Enhanced RAG Integration")
    print("=" * 40)
    
    if enhanced_rag.available:
        print("✅ Enhanced RAG is available")
        
        # Test search
        results = search_fvi_knowledge("coal dependency infrastructure", top_k=3)
        print(f"\\n📊 Search test: Found {len(results)} results")
        for i, result in enumerate(results):
            score = result.get('relevance_score', 0)
            content = result.get('content', 'No content')[:100]
            print(f"  {i+1}. Score: {score:.3f} - {content}...")
        
        # Test country context
        country_context = enhanced_rag.get_context_for_country("China", "coal assessment")
        print(f"\\n🌏 China context preview: {country_context[:200]}...")
        
        # Print stats
        stats = enhanced_rag.get_stats()
        print(f"\\n📈 Stats: {stats}")
        
    else:
        print("❌ Enhanced RAG is not available")
        print("Please run create_full_vectorstore.py first")
