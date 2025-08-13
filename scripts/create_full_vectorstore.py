# create_full_vectorstore.py - Create comprehensive FVI vectorstore
"""
Create a comprehensive vectorstore with the full FVI knowledge base and score data
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import json
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FVIVectorstoreBuilder:
    """Builder for comprehensive FVI vectorstore"""
    
    def __init__(self, vectorstore_dir="vectorstore", model_name="all-MiniLM-L6-v2"):
        self.vectorstore_dir = Path(vectorstore_dir)
        self.vectorstore_dir.mkdir(exist_ok=True)
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        
        # Storage
        self.documents = []
        self.metadata = []
        self.embeddings = []
        
    def add_knowledge_base(self, knowledge_file):
        """Add knowledge base text to vectorstore"""
        try:
            if not os.path.exists(knowledge_file):
                logger.error(f"Knowledge file not found: {knowledge_file}")
                return False
            
            logger.info(f"Processing knowledge file: {knowledge_file}")
            
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into chunks (simple chunking)
            chunk_size = 1000
            overlap = 200
            
            chunks = []
            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk.strip())
            
            logger.info(f"Split knowledge base into {len(chunks)} chunks")
            
            # Process chunks
            for i, chunk in enumerate(chunks):
                if len(chunk) > 50:  # Skip very short chunks
                    self.documents.append(chunk)
                    self.metadata.append({
                        'source': 'fvi_knowledge',
                        'type': 'knowledge',
                        'chunk_id': i,
                        'content': chunk[:200] + "..." if len(chunk) > 200 else chunk
                    })
            
            logger.info(f"Added {len(chunks)} knowledge chunks to vectorstore")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add knowledge base: {e}")
            return False
    
    def add_sample_scores(self):
        """Add sample FVI scores to vectorstore"""
        try:
            logger.info("Creating sample FVI scores data")
            
            countries = ['China', 'India', 'United States', 'Germany', 'Poland', 'Australia', 'South Africa', 'Indonesia']
            dimensions = ['infrastructure', 'necessity', 'resource', 'artificial_support', 'ecological', 'economic', 'emissions']
            
            for country in countries:
                # Create realistic sample scores
                base_score = np.random.uniform(30, 80)
                
                scores = {}
                for dim in dimensions:
                    # Add some variation per dimension
                    variation = np.random.uniform(-20, 20)
                    score = max(0, min(100, base_score + variation))
                    scores[dim] = round(score, 2)
                
                overall_score = round(np.mean(list(scores.values())), 2)
                
                # Create descriptive text
                score_text = f"""
                Country Assessment: {country}
                Overall FVI Score: {overall_score}
                
                Dimension Scores:
                - Infrastructure: {scores['infrastructure']} (coal dependency and transition readiness)
                - Necessity: {scores['necessity']} (energy security and essential needs)
                - Resource: {scores['resource']} (coal reserves and production capacity)
                - Artificial Support: {scores['artificial_support']} (government subsidies and policy support)
                - Ecological: {scores['ecological']} (environmental impact and sustainability)
                - Economic: {scores['economic']} (market viability and financial risks)
                - Emissions: {scores['emissions']} (carbon footprint and climate compliance)
                
                This assessment provides insights into {country}'s coal industry viability across multiple dimensions.
                The overall score of {overall_score} indicates {'high' if overall_score > 70 else 'moderate' if overall_score > 40 else 'low'} viability.
                """
                
                self.documents.append(score_text)
                self.metadata.append({
                    'source': 'fvi_scores',
                    'type': 'country_scores',
                    'country': country,
                    'overall_score': overall_score,
                    'scores': scores,
                    'content': f"{country} FVI Assessment - Overall Score: {overall_score}"
                })
            
            logger.info(f"Added sample scores for {len(countries)} countries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add sample scores: {e}")
            return False
    
    def create_embeddings(self):
        """Create embeddings for all documents"""
        try:
            if not self.documents:
                logger.error("No documents to embed")
                return False
            
            logger.info(f"Creating embeddings for {len(self.documents)} documents")
            
            # Create embeddings in batches
            batch_size = 32
            all_embeddings = []
            
            for i in range(0, len(self.documents), batch_size):
                batch = self.documents[i:i + batch_size]
                batch_embeddings = self.model.encode(batch, show_progress_bar=True)
                all_embeddings.extend(batch_embeddings)
            
            self.embeddings = np.array(all_embeddings)
            logger.info(f"Created embeddings with shape: {self.embeddings.shape}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            return False
    
    def build_faiss_index(self):
        """Build FAISS index from embeddings"""
        try:
            if len(self.embeddings) == 0:
                logger.error("No embeddings available for indexing")
                return False
            
            logger.info("Building FAISS index")
            
            # Normalize embeddings for cosine similarity
            normalized_embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            
            # Create FAISS index
            dimension = self.embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Add embeddings to index
            index.add(normalized_embeddings.astype(np.float32))
            
            logger.info(f"FAISS index built with {index.ntotal} vectors")
            return index
            
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
            return None
    
    def save_vectorstore(self, index):
        """Save the complete vectorstore"""
        try:
            logger.info("Saving vectorstore files")
            
            # Save FAISS index
            faiss_path = self.vectorstore_dir / "index.faiss"
            faiss.write_index(index, str(faiss_path))
            logger.info(f"Saved FAISS index: {faiss_path}")
            
            # Save metadata
            metadata_path = self.vectorstore_dir / "metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info(f"Saved metadata: {metadata_path}")
            
            # Save index information
            index_info = {
                "version": "2.0",
                "embedding_model": self.model_name,
                "documents_count": len(self.documents),
                "dimension": int(self.embeddings.shape[1]),
                "faiss_available": True,
                "chromadb_available": False,
                "created_at": pd.Timestamp.now().isoformat(),
                "status": "active",
                "description": "FVI System comprehensive vectorstore with knowledge base and score data"
            }
            
            index_json_path = self.vectorstore_dir / "index.json"
            with open(index_json_path, 'w') as f:
                json.dump(index_info, f, indent=2)
            logger.info(f"Saved index info: {index_json_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save vectorstore: {e}")
            return False
    
    def test_search(self, index):
        """Test the search functionality"""
        try:
            logger.info("Testing search functionality")
            
            test_queries = [
                "coal industry infrastructure dependency",
                "energy security and transition",
                "environmental impact ecological",
                "China coal assessment",
                "emissions carbon footprint"
            ]
            
            for query in test_queries:
                # Create query embedding
                query_embedding = self.model.encode([query])
                query_normalized = query_embedding / np.linalg.norm(query_embedding)
                
                # Search
                scores, indices = index.search(query_normalized.astype(np.float32), 3)
                
                print(f"\\nQuery: '{query}'")
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx < len(self.metadata):
                        metadata = self.metadata[idx]
                        content = metadata.get('content', 'No content')
                        print(f"  {i+1}. Score: {score:.3f} - {content}")
            
            return True
            
        except Exception as e:
            logger.error(f"Search test failed: {e}")
            return False

def main():
    """Main function to build comprehensive vectorstore"""
    print("🚀 FVI Comprehensive Vectorstore Builder")
    print("=" * 50)
    
    try:
        # Initialize builder
        builder = FVIVectorstoreBuilder()
        
        # Add knowledge base
        knowledge_file = "vectorstore/fvi_knowledge.txt"
        if not builder.add_knowledge_base(knowledge_file):
            print(f"❌ Failed to add knowledge base from {knowledge_file}")
            return 1
        
        # Add sample scores
        if not builder.add_sample_scores():
            print("❌ Failed to add sample scores")
            return 1
        
        # Create embeddings
        if not builder.create_embeddings():
            print("❌ Failed to create embeddings")
            return 1
        
        # Build FAISS index
        index = builder.build_faiss_index()
        if index is None:
            print("❌ Failed to build FAISS index")
            return 1
        
        # Save vectorstore
        if not builder.save_vectorstore(index):
            print("❌ Failed to save vectorstore")
            return 1
        
        # Test search
        if not builder.test_search(index):
            print("❌ Search test failed")
            return 1
        
        print("\\n🎉 Comprehensive vectorstore created successfully!")
        print("\\n📁 Generated files:")
        print("  - vectorstore/index.faiss (FAISS vector index)")
        print("  - vectorstore/metadata.pkl (document metadata)")
        print("  - vectorstore/index.json (index information)")
        
        print(f"\\n📊 Statistics:")
        print(f"  - Total documents: {len(builder.documents)}")
        print(f"  - Embedding dimension: {builder.embeddings.shape[1]}")
        print(f"  - Knowledge chunks: {len([m for m in builder.metadata if m['type'] == 'knowledge'])}")
        print(f"  - Country assessments: {len([m for m in builder.metadata if m['type'] == 'country_scores'])}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to build vectorstore: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
