# main.py - Enhanced FVI System Main Interface
"""
Enhanced FVI System with Complete Data Loading and LangChain Integration
This system provides comprehensive coal industry viability assessment with intelligent RAG capabilities.
Streamlit FVI System Application
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yaml
import os
import logging
import requests
import json
from datetime import datetime

# NumPy 2.0 compatibility setup
try:
    from numpy2_compatibility import setup_numpy2_compatibility
    setup_numpy2_compatibility()
except ImportError:
    # Manual setup if compatibility module not found
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="numpy")
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Import custom modules
from fvi_aggregator import FVI_Aggregator

# Make RAGAgent import optional (we use backend /api/chat now)
try:
    from rag_agent import RAGAgent  # optional; not required for backend call
except Exception:
    RAGAgent = None

from data_loader import load_all_data

# Import enhanced RAG integration (optional; layout unchanged)
try:
    from enhanced_rag_integration import enhanced_rag, get_enhanced_context, is_enhanced_rag_available
    ENHANCED_RAG_AVAILABLE = True
except ImportError:
    ENHANCED_RAG_AVAILABLE = False
    logging.warning("Enhanced RAG integration not available")

# Page configuration
st.set_page_config(
    page_title="FVI System - Coal Industry Viability Index",
    layout="wide",
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# Setup logging
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/fvi.log"),
        logging.StreamHandler()  # Also log to console
    ]
)

# Custom CSS for better styling (unchanged)
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f4e79;
    }
    .persona-info {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header (unchanged)
st.markdown('<h1 class="main-header">Future Viability Index (FVI)</h1>', unsafe_allow_html=True)
st.markdown("*Comprehensive Coal Industry Viability Assessment Platform*")

# Load configuration
@st.cache_data
def load_config():
    # First try in current directory
    for config_file in ["config.yaml", "config.yml"]:
        try:
            if os.path.exists(config_file):
                with open(config_file) as f:
                    return yaml.safe_load(f)
        except Exception:
            pass
    
    # Try sibling/parent directories
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
        if os.path.exists(config_path):
            with open(config_path) as f:
                return yaml.safe_load(f)
    except Exception:
        pass

    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
        if os.path.exists(config_path):
            with open(config_path) as f:
                return yaml.safe_load(f)
    except Exception as e:
        st.error(f"Failed to load configuration: {e}")
        # Default minimal config
        return {
            "persona_weights": {
                "analyst": {"infrastructure": 0.143, "necessity": 0.143, "resource": 0.143, 
                           "artificial_support": 0.143, "ecological": 0.143, "economic": 0.143, "emissions": 0.143},
                "investor": {"economic": 0.25, "artificial_support": 0.20, "emissions": 0.20, 
                            "infrastructure": 0.15, "resource": 0.10, "ecological": 0.05, "necessity": 0.05},
                "policy_maker": {"necessity": 0.20, "economic": 0.20, "emissions": 0.20, 
                                "infrastructure": 0.15, "ecological": 0.15, "artificial_support": 0.05, "resource": 0.05},
                "ngo": {"emissions": 0.25, "ecological": 0.25, "necessity": 0.20, 
                       "infrastructure": 0.10, "resource": 0.10, "artificial_support": 0.05, "economic": 0.05},
                "citizen": {"necessity": 0.25, "ecological": 0.20, "infrastructure": 0.20, 
                           "economic": 0.15, "emissions": 0.10, "artificial_support": 0.05, "resource": 0.05}
            },
            "data_dir": "data",
            "vectorstore_dir": "vectorstore"
        }

config = load_config()

# =========================
# API Configuration (UPDATED)
# =========================
# Point to your new backend on 8080
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# API Connection Functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_countries_data(persona="analyst"):
    """Get country data from API (if available); otherwise fallback later."""
    try:
        # Note: your new backend may not have this endpoint; fallback will handle it.
        response = requests.get(f"{API_BASE_URL}/api/countries", 
                                params={"persona": persona}, 
                                timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None

@st.cache_data(ttl=300)
def get_system_info():
    """Get system info (optional)"""
    try:
        response = requests.get(f"{API_BASE_URL}/healthz", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None

def chat_with_rag(message, persona="analyst"):
    """Chat with backend RAG API (UPDATED to new response shape)."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={"message": message, "persona": persona},
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            # Map new schema to what the UI expects
            return {
                "response": data.get("text", ""),
                "sources": [],  # backend doesn't return sources
                "persona": data.get("persona", persona),
                "meta": data.get("meta", {})
            }
        else:
            return {"response": "Sorry, I couldn't process your request.", "sources": [], "persona": persona}
    except requests.exceptions.RequestException as e:
        return {"response": f"Connection error: {e}", "sources": [], "persona": persona}

# Sidebar configuration (unchanged)
with st.sidebar:
    st.image("assets/logo.png" if os.path.exists("assets/logo.png") else "https://via.placeholder.com/150x75/1f4e79/white?text=FVI", width=150)
    
    st.header("🔧 System Configuration")
    
    # Persona selection
    persona_options = list(config.get("persona_weights", {}).keys())
    if not persona_options:
        persona_options = ["analyst", "investor", "policy_maker", "ngo", "citizen"]
    
    selected_persona = st.selectbox(
        "Select Analysis Perspective",
        persona_options,
        index=0,
        help="Choose the perspective for FVI calculation weighting"
    )
    
    # Display persona weights
    if selected_persona and config.get("persona_weights"):
        st.markdown("### Current Weights")
        weights = config["persona_weights"][selected_persona]
        for dimension, weight in weights.items():
            st.write(f"**{dimension.replace('_', ' ').title()}**: {weight:.1%}")
    
    st.divider()
    
    # System information (updated to use /healthz if present)
    st.markdown("###System Info")
    health = get_system_info()
    if health and health.get("status") == "ok":
        st.success("✅ Backend Online")
        st.caption(f"Model: {health.get('model', 'n/a')} | Vectorstore: {health.get('vectorstore_dir', 'n/a')}")
    else:
        st.warning("⚠️ Backend Unavailable — using local fallback data")
    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Load and process data from API
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_scores_data(persona="analyst"):
    """Load FVI scores from API if available; otherwise fallback locally."""
    try:
        countries_data = get_countries_data(persona)
        if countries_data:
            # Convert API response to DataFrame
            df_data = []
            for country_info in countries_data:
                df_data.append({
                    'Country': country_info['country'],
                    'Infrastructure': country_info['infrastructure'],
                    'Necessity': country_info['necessity'],
                    'Resource': country_info['resource'],
                    'Artificial_Support': country_info['artificial_support'],
                    'Ecological': country_info['ecological'],
                    'Economic': country_info['economic'],
                    'Emissions': country_info['emissions'],
                    'FVI': country_info['fvi'],
                    'Rank': country_info.get('rank', 0),
                    'Viability': country_info.get('viability_level', 'Medium')
                })
            
            scores_df = pd.DataFrame(df_data)
            scores_df.set_index('Country', inplace=True)
            
            # Ensure numeric columns are properly typed for NumPy 2.0 compatibility
            numeric_cols = ['Infrastructure', 'Necessity', 'Resource', 'Artificial_Support', 
                            'Ecological', 'Economic', 'Emissions', 'FVI', 'Rank']
            for col in numeric_cols:
                if col in scores_df.columns:
                    scores_df[col] = pd.to_numeric(scores_df[col], errors='coerce')
            
            # Create FVI scores series for compatibility
            fvi_scores = pd.Series(scores_df['FVI'].to_dict())
            return scores_df, fvi_scores
        else:
            # Fallback data if API is not available
            return load_fallback_data()
            
    except Exception as e:
        st.error(f"Error loading data from API: {e}")
        return load_fallback_data()

def load_fallback_data():
    """Fallback data when API is not available"""
    try:
        # Import scoring functions
        from scores import (
            calculate_infrastructure_score,
            calculate_necessity_score,
            calculate_resource_score,
            calculate_artificial_support_score,
            calculate_ecological_score,
            calculate_economic_score,
            calculate_emissions_score
        )
        
        # Load all data
        data = load_all_data(config)
        
        # Define countries for analysis
        countries = ["India", "China", "Germany", "USA", "Australia", "Indonesia", "South Africa", "Poland"]
        
        # Calculate scores for each dimension
        scores_dict = {
            "Infrastructure": calculate_infrastructure_score(data.get('infrastructure', {}), countries),
            "Necessity": calculate_necessity_score(data.get('necessity', {}), countries),
            "Resource": calculate_resource_score(data.get('resource', {}), countries),
            "Artificial_Support": calculate_artificial_support_score(data.get('artificial_support', {}), countries),
            "Ecological": calculate_ecological_score(data.get('ecological', {}), countries),
            "Economic": calculate_economic_score(data.get('economic', {}), countries),
            "Emissions": calculate_emissions_score(data.get('emissions', {}), countries)
        }
        
        # Create DataFrame
        scores_df = pd.DataFrame(scores_dict)
        
        # Fill any missing values with median and ensure numeric types for NumPy 2.0
        for col in scores_df.columns:
            scores_df[col] = pd.to_numeric(scores_df[col], errors='coerce')
        scores_df = scores_df.fillna(scores_df.median())
        
        # Create FVI scores - simple average for fallback
        fvi_scores = scores_df.mean(axis=1)
        
        return scores_df, fvi_scores
        
    except Exception as e:
        st.error(f"Error calculating scores: {e}")
        logging.error(f"Score calculation failed: {e}")
        
        # Fallback to sample data
        scores_df = pd.DataFrame({
            "Infrastructure": [65, 85, 45, 50, 75, 80, 85, 60],
            "Necessity": [75, 80, 40, 55, 65, 85, 90, 70],
            "Resource": [70, 85, 45, 75, 90, 75, 60, 55],
            "Artificial_Support": [65, 80, 25, 45, 70, 75, 80, 55],
            "Ecological": [40, 30, 75, 55, 58, 42, 48, 62],
            "Economic": [60, 80, 25, 45, 55, 70, 75, 58],
            "Emissions": [32, 25, 75, 68, 55, 42, 28, 45]
        }, index=["India", "China", "Germany", "USA", "Australia", "Indonesia", "South Africa", "Poland"])
        
        # Ensure all columns are numeric for NumPy 2.0 compatibility
        for col in scores_df.columns:
            scores_df[col] = pd.to_numeric(scores_df[col], errors='coerce')
        
        # Calculate FVI as mean of all dimensions
        fvi_scores = scores_df.mean(axis=1)
        
        return scores_df, fvi_scores

# Initialize RAG agent (kept for layout symmetry; not required for backend call)
@st.cache_resource
def get_rag_agent():
    """Initialize and cache RAG agent with enhanced capabilities (optional/local)."""
    try:
        if RAGAgent is None:
            raise RuntimeError("Local RAGAgent not available; using backend API.")
        rag = RAGAgent()
        
        # Enhanced RAG status info (optional)
        if ENHANCED_RAG_AVAILABLE and is_enhanced_rag_available():
            rag.enhanced_available = True
            rag.enhanced_stats = enhanced_rag.get_stats()
            logging.info("RAG agent initialized with enhanced vectorstore")
        else:
            rag.enhanced_available = False
            logging.info("RAG agent initialized with basic functionality")
        return rag
    except Exception as e:
        st.info("Using backend API for RAG.")
        return None

# Main application (layout unchanged, RAG call updated)
def main():
    # Load data with selected persona
    scores_df, fvi_scores = load_scores_data(selected_persona)
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("FVI Dashboard")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["FVI Rankings", "Detailed Scores", "Country Comparison"])
        
        with tab1:
            st.markdown("### Coal Industry Viability Rankings")
            st.markdown(f"*Analysis from **{selected_persona.replace('_', ' ').title()}** perspective*")
            
            # Sort countries by FVI (lower = better viability)
            fvi_ranking = fvi_scores.sort_values()
            
            # Display as horizontal bar chart
            st.bar_chart(fvi_ranking)
            
            # Display ranking table
            ranking_df = pd.DataFrame({
                'Country': fvi_ranking.index,
                'FVI Score': fvi_ranking.values,
                'Viability': ['High' if score < 40 else 'Medium' if score < 60 else 'Low' for score in fvi_ranking.values],
                'Rank': range(1, len(fvi_ranking) + 1)
            })
            
            st.dataframe(
                ranking_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "FVI Score": st.column_config.NumberColumn(
                        "FVI Score",
                        help="Lower scores indicate better coal viability",
                        format="%.1f"
                    ),
                    "Viability": st.column_config.TextColumn(
                        "Viability Level",
                        help="Viability assessment based on FVI score"
                    )
                }
            )
        
        with tab2:
            st.markdown("### Detailed Dimension Scores")
            
            # Heatmap-style display
            st.dataframe(
                scores_df.round(1),
                use_container_width=True,
                column_config={col: st.column_config.NumberColumn(
                    col.replace('_', ' ').title(),
                    format="%.1f"
                ) for col in scores_df.columns}
            )
            
            # Dimension analysis
            st.markdown("### Dimension Analysis")
            # Filter only numeric columns for mean calculation (NumPy 2.0 compatibility)
            numeric_columns = scores_df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 0:
                dimension_avg = scores_df[numeric_columns].mean().sort_values(ascending=False)
            else:
                # Fallback if no numeric columns
                dimension_avg = pd.Series(dtype=float)
            
            col_a, col_b = st.columns(2)
            if len(dimension_avg) > 0:
                with col_a:
                    st.metric("Highest Scoring Dimension", dimension_avg.index[0], f"{dimension_avg.iloc[0]:.1f}")
                with col_b:
                    st.metric("Lowest Scoring Dimension", dimension_avg.index[-1], f"{dimension_avg.iloc[-1]:.1f}")
            else:
                with col_a:
                    st.metric("Highest Scoring Dimension", "N/A", "0.0")
                with col_b:
                    st.metric("Lowest Scoring Dimension", "N/A", "0.0")
        
        with tab3:
            st.markdown("### Country Comparison")
            
            selected_countries = st.multiselect(
                "Select countries to compare:",
                scores_df.index.tolist(),
                default=scores_df.index[:4].tolist()
            )
            
            if selected_countries:
                comparison_df = scores_df.loc[selected_countries]
                
                # Radar chart would be ideal here, but using line chart for simplicity
                st.line_chart(comparison_df.T)
                
                # Summary statistics
                st.markdown("#### Summary Statistics")
                summary_stats = comparison_df.describe().round(1)
                st.dataframe(summary_stats, use_container_width=True)
    
    with col2:
        st.subheader("FVI Intelligence Chat")
        
        # Initialize chat agent (not used directly; keeps layout parity)
        rag_agent = get_rag_agent()
        
        # Chat interface
        user_question = st.text_area(
            "Ask about coal industry viability:",
            placeholder=f"As a {selected_persona}, what are the key risks for coal investment in India?",
            height=100
        )
        
        # Optional country selection for context (kept)
        selected_country = st.selectbox(
            "Focus on specific country (optional):",
            ["Any", "China", "India", "United States", "Germany", "Poland", "Australia", "South Africa", "Indonesia"],
            index=0
        )
        
        if st.button("Analyze", use_container_width=True):
            if user_question.strip():
                with st.spinner("Analyzing your question..."):
                    try:
                        # Enhanced context (optional/local; kept as-is)
                        enhanced_context = None
                        if ENHANCED_RAG_AVAILABLE and is_enhanced_rag_available():
                            country_filter = None if selected_country == "Any" else selected_country
                            enhanced_context = get_enhanced_context(
                                user_question, 
                                country=country_filter, 
                                persona=selected_persona
                            )
                        
                        # Use backend API for RAG chat (UPDATED)
                        result = chat_with_rag(user_question, selected_persona)
                        
                        st.markdown("### Analysis Result")
                        st.write(result.get("response", "No response generated."))
                        
                        # show token usage if available
                        meta = result.get("meta") or {}
                        usage = meta.get("usage") or {}
                        if usage:
                            st.caption(f"Tokens — prompt: {usage.get('prompt_tokens')}, completion: {usage.get('completion_tokens')}, total: {usage.get('total_tokens')}")
                        
                        # Show enhanced context if available (unchanged)
                        if enhanced_context and enhanced_context.get("enhanced"):
                            with st.expander("Enhanced Context Analysis", expanded=False):
                                
                                # Key Insights Section
                                if enhanced_context.get("key_insights"):
                                    st.markdown("### Key Insights")
                                    for i, insight in enumerate(enhanced_context["key_insights"], 1):
                                        st.info(f"**{i}.** {insight}")
                                
                                # Structured Categories
                                structured_context = enhanced_context.get("structured_context", {})
                                categories = structured_context.get("categories", {})
                                
                                if categories:
                                    st.markdown("### Context by Category")
                                    
                                    # Create tabs for different categories
                                    category_names = list(categories.keys())
                                    category_labels = {
                                        "industry_overview": "Industry Overview",
                                        "technical_data": "Technical Data", 
                                        "economic_factors": "Economic Factors",
                                        "environmental_impact": "Environmental Impact",
                                        "policy_regulatory": "Policy & Regulatory",
                                        "market_trends": "Market Trends",
                                        "country_specific": "Country-Specific"
                                    }
                                    
                                    if len(category_names) > 0:
                                        # Create tabs dynamically based on available categories
                                        tab_labels = [category_labels.get(cat, cat.replace('_', ' ').title()) for cat in category_names]
                                        tabs = st.tabs(tab_labels)
                                        
                                        for i, (category, items) in enumerate(categories.items()):
                                            with tabs[i]:
                                                if items:
                                                    for j, item in enumerate(items, 1):
                                                        relevance = item.get('relevance', 0)
                                                        source = item.get('source', 'Unknown')
                                                        content = item.get('content', '')
                                                        
                                                        # Display with relevance indicator
                                                        relevance_color = "🟢" if relevance > 0.7 else "🟡" if relevance > 0.5 else "🔴"
                                                        
                                                        with st.container():
                                                            col1, col2 = st.columns([4, 1])
                                                            with col1:
                                                                st.markdown(f"**Context {j}:**")
                                                                st.write(content[:400] + "..." if len(content) > 400 else content)
                                                            with col2:
                                                                st.metric("Relevance", f"{relevance:.2f}", delta=None)
                                                                st.caption(f"Source: {source}")
                                                        st.divider()
                                                else:
                                                    st.info("No relevant context found for this category.")
                                
                                # Country-Specific Context
                                if enhanced_context.get("country_context"):
                                    st.markdown("### Country-Specific Analysis")
                                    with st.container():
                                        st.markdown("**Detailed Country Context:**")
                                        country_text = enhanced_context["country_context"]
                                        
                                        # Format country context better
                                        if "Assessment" in country_text:
                                            parts = country_text.split("Assessment")
                                            if len(parts) > 1:
                                                st.markdown(f"**Assessment:** {parts[1]}")
                                        else:
                                            st.write(country_text)
                                
                                # Summary Statistics
                                st.markdown("### Analysis Summary")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric(
                                        "Documents Retrieved", 
                                        enhanced_context.get('relevant_documents', 0)
                                    )
                                
                                with col2:
                                    st.metric(
                                        "Active Categories", 
                                        len(categories)
                                    )
                                
                                with col3:
                                    st.metric(
                                        "Key Insights", 
                                        len(enhanced_context.get("key_insights", []))
                                    )
                                
                                # Data Sources
                                data_sources = structured_context.get("data_sources", [])
                                if data_sources:
                                    st.markdown("**Data Sources:**")
                                    for source in data_sources:
                                        st.markdown(f"• {source}")
                        
                        # Show sources if available (backend returns none; kept for compatibility)
                        if result.get("sources"):
                            with st.expander("Sources"):
                                for i, source in enumerate(result["sources"]):
                                    st.write(f"**Source {i+1}**: {source}")
                        
                        # Show timestamp (backend doesn't provide; kept if present)
                        if result.get("timestamp"):
                            st.caption(f"Response generated at: {result['timestamp']}")
                            
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
                        st.info("💡 Tip: Ensure the backend API is running and RAG system is properly configured")
            else:
                st.warning("Please enter a question to analyze.")
        
        # Quick insights panel (unchanged)
        st.markdown("---")
        st.markdown("### Quick Insights")
        
        # Best and worst countries for current persona
        best_country = fvi_scores.idxmin()
        worst_country = fvi_scores.idxmax()
        
        st.success(f"**Most Viable**: {best_country} (FVI: {fvi_scores[best_country]:.1f})")
        st.error(f"**Least Viable**: {worst_country} (FVI: {fvi_scores[worst_country]:.1f})")
        
        # Persona-specific insight
        persona_insights = {
            "investor": "Focus on economic returns and artificial support levels",
            "policy_maker": "Consider necessity and emissions for policy decisions",
            "ngo": "Prioritize emissions and ecological impact",
            "analyst": "Balanced view across all dimensions",
            "citizen": "Emphasize necessity and local ecological impact"
        }
        
        st.info(f"**{selected_persona.title()} Focus**: {persona_insights.get(selected_persona, 'Comprehensive analysis across all dimensions')}")

def generate_data_insights(persona, question, fvi_scores, scores_df):
    """Generate insights based on current data when RAG is not available"""
    
    # Extract country mentions from question
    countries_mentioned = [country for country in scores_df.index if country.lower() in question.lower()]
    
    if countries_mentioned:
        country = countries_mentioned[0]
        country_data = scores_df.loc[country]
        fvi_score = fvi_scores[country]
        
        # Get dimension rankings for this country
        dimensions_ranked = country_data.sort_values(ascending=False)
        
        insights = f"""
        **{country} Analysis from {persona.title()} Perspective:**
        
        • **Overall FVI Score**: {fvi_score:.1f} ({'High' if fvi_score < 40 else 'Medium' if fvi_score < 60 else 'Low'} viability)
        
        • **Strongest Dimensions**:
          - {dimensions_ranked.index[0]}: {dimensions_ranked.iloc[0]:.1f}
          - {dimensions_ranked.index[1]}: {dimensions_ranked.iloc[1]:.1f}
        
        • **Weakest Dimensions**:
          - {dimensions_ranked.index[-1]}: {dimensions_ranked.iloc[-1]:.1f}
          - {dimensions_ranked.index[-2]}: {dimensions_ranked.iloc[-2]:.1f}
        
        • **Rank Among Countries**: {(fvi_scores < fvi_score).sum() + 1} out of {len(fvi_scores)}
        """
    else:
        # General insights
        best_country = fvi_scores.idxmin()
        insights = f"""
        **General FVI Insights from {persona.title()} Perspective:**
        
        • **Most Viable Country**: {best_country} (FVI: {fvi_scores[best_country]:.1f})
        • **Average FVI Score**: {fvi_scores.mean():.1f}
        • **Countries with High Viability** (FVI < 50): {', '.join(fvi_scores[fvi_scores < 50].index)}
        
        The analysis considers all 7 dimensions with weights specific to {persona} priorities.
        """
    
    return insights

if __name__ == "__main__":
    main()
