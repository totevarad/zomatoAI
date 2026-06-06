import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from app.config import get_settings
from app.store import RestaurantStore
from app.recommend_service import deterministic_recommend
from app.schemas import RecommendRequest, BudgetBand

# --- Page Config ---
st.set_page_config(
    page_title="Zomato AI",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Hide Streamlit Header, Footer, and make iframe full viewport ---
st.markdown("""
<style>
    /* Hide Streamlit branding and navigation */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}
    div[data-testid="stHeader"] {display: none;}
    
    /* Reset padding/margin of block container */
    .main .block-container {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
        max-width: 100% !important;
        height: 100vh !important;
    }
    
    /* Full screen iframe styling */
    iframe[title*="zomato_ai_dashboard"] {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw !important;
        height: 100vh !important;
        border: none;
        margin: 0;
        padding: 0;
        z-index: 999999;
        background-color: #131313;
    }
    
    /* Hide scrollbar of the parent body */
    body {
        overflow: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

# --- App Logic ---
settings = get_settings()
db_path = Path(settings.database_path)

# Automatically run ingest if SQLite DB does not exist
if not db_path.is_file():
    with st.spinner("⏳ First-time setup: Ingesting dataset from Hugging Face... (takes a few seconds)"):
        try:
            from app.ingest import ingest_to_sqlite
            ingest_to_sqlite(db_path, settings)
        except Exception as e:
            st.error(f"Failed to ingest dataset: {e}")

# Initialize store
store = RestaurantStore(db_path)

# Initialize recommendations and request tracking in session state
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None

# Declare custom component pointing to static/
_my_component = components.declare_component(
    "zomato_ai_dashboard",
    path=str(Path(__file__).parent / "static")
)

# Render component
val = _my_component(results=st.session_state.recommendations)

# Handle recommendation requests from frontend
if val and val.get("action") == "recommend":
    request_id = val.get("requestId")
    # Only process if this request has a new ID
    if request_id != st.session_state.last_request_id:
        st.session_state.last_request_id = request_id
        req_data = val.get("data", {})
        try:
            request_body = RecommendRequest(
                location=req_data.get("location"),
                cuisine=req_data.get("cuisine"),
                budget=BudgetBand(req_data.get("budget")),
                top_n=int(req_data.get("top_n", 5)),
                min_rating=float(req_data.get("min_rating", 3.5)),
                notes=req_data.get("notes") or None
            )
            
            # Get recommendations
            response = deterministic_recommend(store, request_body, settings=settings)
            
            # Serialize response to JSON dict safely
            if hasattr(response, "model_dump"):
                serialized_results = response.model_dump(mode="json")
            else:
                serialized_results = response.dict()
                
            st.session_state.recommendations = serialized_results
            st.rerun()
        except Exception as e:
            st.session_state.recommendations = {
                "results": [],
                "meta": {
                    "candidate_count": 0,
                    "model": None,
                    "phase": "deterministic",
                    "message": f"Error compiling recommendations: {e}"
                }
            }
            st.rerun()
