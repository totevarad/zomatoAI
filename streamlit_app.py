import streamlit as st
from pathlib import Path
from app.config import get_settings
from app.store import RestaurantStore
from app.recommend_service import deterministic_recommend
from app.schemas import RecommendRequest, BudgetBand

# --- Page Config ---
st.set_page_config(
    page_title="Zomato AI Recommender",
    page_icon="🍽️",
    layout="wide",
)

# --- App Styling ---
st.markdown("""
<style>
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
    }
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF5252, #FF8A80);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #BDBDBD;
        margin-bottom: 2rem;
    }
    .restaurant-card {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #333;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .restaurant-card:hover {
        border-color: #FF5252;
        transform: translateY(-3px);
        box-shadow: 0 4px 20px rgba(255, 82, 82, 0.15);
    }
    .rating-badge {
        background-color: #4CAF50;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .cuisine-tag {
        color: #9E9E9E;
        font-size: 0.9rem;
        margin-top: 4px;
    }
    .explanation-box {
        background-color: rgba(255, 82, 82, 0.05);
        border-left: 3px solid #FF5252;
        padding: 10px 15px;
        margin-top: 12px;
        border-radius: 0 4px 4px 0;
    }
    .explanation-text {
        font-style: italic;
        color: #FFAB91;
        font-size: 0.95rem;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- App Logic ---
settings = get_settings()
db_path = Path(settings.database_path)
store = RestaurantStore(db_path)

def main():
    st.markdown('<div class="main-header">Zomato AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Hyper-personalized restaurant recommendations grounded in data.</div>', unsafe_allow_html=True)

    # --- Sidebar Filters ---
    with st.sidebar:
        st.markdown("### 🔍 Search Filters")
        
        location = st.text_input("Area in Bangalore", value="Banashankari", help="e.g. Indiranagar, Koramangala")
        cuisine = st.text_input("Cuisine", value="Chinese", help="e.g. North Indian, Italian")
        budget = st.selectbox("Budget Range", options=["low", "medium", "high"], index=1)
        
        st.markdown("---")
        st.markdown("### 🛠️ Advanced")
        top_n = st.number_input("Recommendations count", min_value=1, max_value=20, value=5)
        min_rating = st.slider("Minimum Rating", min_value=0.0, max_value=5.0, value=3.5, step=0.1)
        extra_context = st.text_area("AI Context", placeholder="e.g. quiet place for a date, family friendly", help="Optional: helps the AI explain why these match your vibe.")

        st.markdown("---")
        search_clicked = st.button("Find My Next Meal", type="primary", use_container_width=True)

    # --- Results ---
    if search_clicked:
        with st.spinner("✨ Curating your personalized list..."):
            request_body = RecommendRequest(
                location=location,
                cuisine=cuisine,
                budget=BudgetBand(budget),
                top_n=top_n,
                min_rating=min_rating,
                extra_context=extra_context
            )
            
            response = deterministic_recommend(store, request_body, settings=settings)
            
            if not response.results:
                st.error("😕 " + (response.meta.message or "No restaurants found matching your criteria."))
                st.info("Try broadening your search or lowering the minimum rating.")
            else:
                st.success(f"🎉 Found {response.meta.candidate_count} matches!")
                
                if response.meta.phase == "llm":
                    st.caption(f"🧠 AI-Powered Ranking: {response.meta.model}")
                else:
                    st.caption("⚖️ Deterministic Ranking (No AI API Key found)")
                
                for res in response.results:
                    st.markdown(f"""
                    <div class="restaurant-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="margin: 0; color: #FF5252;">{res.name}</h3>
                            <span class="rating-badge">★ {res.rating}</span>
                        </div>
                        <div class="cuisine-tag">{res.cuisine} • {res.cost_band.value.capitalize()} Budget</div>
                        <div class="explanation-box">
                            <p class="explanation-text">"{res.explanation}"</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        # Hero Section
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            ### Welcome to the future of dining! 🚀
            
            This recommender uses:
            - **Real Data**: 40,000+ cleaned Zomato Bangalore entries.
            - **Hard Filters**: Precise matching on location, cuisine, and budget.
            - **AI Ranking**: (Optional) Groq-powered natural language explanations.
            
            **How to start:**
            1. Enter your preferred **Area** and **Cuisine** in the sidebar.
            2. Adjust your **Budget** and **Rating** thresholds.
            3. Add **Extra Context** if you want the AI to personalize the "Why".
            4. Click **Find My Next Meal**!
            """)
        with col2:
            st.image("https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&q=80&w=1000", caption="Bangalore Dining Scene")

if __name__ == "__main__":
    main()
