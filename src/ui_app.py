"""
Smart Crop Advisor - Streamlit UI Application
User interface for crop recommendation and yield prediction
"""

import streamlit as st
import requests
from auth_system import register_user, login_user
import time
from typing import Dict, Any

# ============================================
# Page Configuration
# ============================================

st.set_page_config(
    page_title="Smart Crop Advisor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# Session State Initialization
# ============================================

if st.query_params.get("logged_in") == "true":
    st.session_state.logged_in = True
elif "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "live_temp" not in st.session_state:
    st.session_state.live_temp = 25.0
    st.session_state.live_humidity = 60.0
    st.session_state.live_rainfall = 100.0

# ============================================
# Authentication Page
# ============================================

def show_auth_page():
    """Display login/registration page"""
    # Custom CSS styling
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        }
        
        .block-container {
            padding-top: 6rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            justify-content: center;
        }

        label p {
            font-size: 18px !important;
            color: #ecf0f1 !important;
        }
        
        input {
            font-size: 18px !important;
            padding: 12px !important;
        }
        
        button p {
            font-size: 18px !important;
            font-weight: bold !important;
        }
        
        .stTabs [data-baseweb="tab-list"] button div {
            font-size: 20px !important;
            font-weight: 600 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown(
            "<h1 style='text-align: center; color: white;'>🌾 Crop classification & Yield Prediction Using Robust Machine Learnign Models for Agriculture Sustainabbility</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align: center; color: #b2bec3; margin-bottom: 2rem;'>Sign in to your AI Agriculture Assistant</p>",
            unsafe_allow_html=True
        )

        tab1, tab2 = st.tabs(["🔒 Login", "📝 Register"])

        # --- LOGIN TAB ---
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input(
                    "Email Address",
                    placeholder="e.g., farmer@example.com"
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••"
                )
                
                submit_button = st.form_submit_button(
                    "Sign In",
                    use_container_width=True
                )

                if submit_button:
                    if not email or not password:
                        st.warning("Please fill out both fields.")
                    elif login_user(email, password):
                        st.session_state.logged_in = True
                        st.session_state.user = email
                        
                        # NEW: Add the flag to the URL
                        st.query_params.logged_in = "true" 
                        
                        st.success("Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid email or password. Please try again.")

        # --- REGISTER TAB ---
        with tab2:
            with st.form("register_form", clear_on_submit=True):
                name = st.text_input(
                    "Full Name",
                    placeholder="e.g., John Doe"
                )
                email_r = st.text_input(
                    "Email Address",
                    placeholder="e.g., farmer@example.com"
                )
                password_r = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a strong password"
                )
                
                submit_r = st.form_submit_button(
                    "Create Account",
                    use_container_width=True
                )

                if submit_r:
                    if not name or not email_r or not password_r:
                        st.warning("Please fill out all fields.")
                    else:
                        success, message = register_user(name, email_r, password_r)
                        if success:
                            st.success("Account created successfully! Logging you in...")
                            time.sleep(1)
                            st.session_state.logged_in = True
                            st.session_state.user = email_r
                            
                            # NEW: Add the flag to the URL
                            st.query_params.logged_in = "true"
                            
                            st.rerun()
                        else:
                            st.error(f"Registration failed: {message}")

# ============================================
# Main Application Page Functions
# ============================================

def fetch_live_weather(city: str) -> Dict[str, Any]:
    """
    Fetch live weather data for a city
    
    Args:
        city: City name
        
    Returns:
        Dictionary with temperature, humidity, and rainfall
    """
    try:
        # Get coordinates
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()
        
        if "results" not in geo_data or not geo_data["results"]:
            return None
        
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        
        # Get weather data
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m&"
            f"daily=precipitation_sum&past_days=30"
        )
        weather_response = requests.get(weather_url, timeout=10)
        weather_data = weather_response.json()
        
        # Extract data
        temp = weather_data["current"]["temperature_2m"]
        humidity = weather_data["current"]["relative_humidity_2m"]
        rainfall = sum(
            r for r in weather_data["daily"]["precipitation_sum"]
            if r is not None
        )
        
        return {
            "temperature": temp,
            "humidity": humidity,
            "rainfall": rainfall
        }
    
    except Exception as e:
        st.sidebar.error(f"Failed to fetch weather data: {str(e)}")
        return None


def get_crop_recommendation(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get crop recommendation from API
    
    Args:
        data: Input features
        
    Returns:
        API response
    """
    try:
        api_base = st.secrets.get("API_BASE_URL", None) if hasattr(st, "secrets") else None
        if not api_base:
            import os
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")

        response = requests.post(
            f"{api_base.rstrip('/')}/recomendCrop",
            json=data,
            timeout=15
        )
        result = response.json()
        
        # Check if API returned an error
        if result.get('error'):
            st.error(f"API Error: {result.get('message', 'Unknown error')}")
            return None
        
        return result
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Make sure the FastAPI backend is running on http://localhost:8000")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ API request timed out. The server may be slow.")
        return None
    except Exception as e:
        st.error(f"❌ Error getting recommendation: {str(e)}")
        return None


def predict_yield(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get yield prediction from API
    
    Args:
        data: Input features
        
    Returns:
        API response
    """
    try:
        api_base = st.secrets.get("API_BASE_URL", None) if hasattr(st, "secrets") else None
        if not api_base:
            import os
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")

        response = requests.post(
            f"{api_base.rstrip('/')}/yieldPrediction",
            json=data,
            timeout=15
        )
        result = response.json()
        
        # Check if API returned an error
        if result.get('error'):
            st.error(f"API Error: {result.get('message', 'Unknown error')}")
            return None
        
        return result
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Make sure the FastAPI backend is running.")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ API request timed out.")
        return None
    except Exception as e:
        st.error(f"❌ Error predicting yield: {str(e)}")
        return None


def show_main_app():
    """Display main application interface"""
    st.title("🌾 Crop Recommendation & Yield Prediction")
    st.write("AI-Based Agriculture Assistant")
    
    # --- Sidebar: Weather Input Mode ---
    st.sidebar.header("🌍 Location & Weather")
    weather_mode = st.sidebar.radio(
        "Weather Input Method",
        ["Manual Entry", "Live Weather"]
    )
    
    if weather_mode == "Live Weather":
        city = st.sidebar.text_input(
            "Enter your City",
            placeholder="e.g., Hyderabad"
        )
        
        if st.sidebar.button("Fetch Live Weather", use_container_width=True):
            weather_data = fetch_live_weather(city)
            if weather_data:
                st.session_state.live_temp = weather_data["temperature"]
                st.session_state.live_humidity = weather_data["humidity"]
                st.session_state.live_rainfall = weather_data["rainfall"]
                st.sidebar.success(f"Weather updated for {city.title()}!")
        
        temperature = st.sidebar.number_input(
            "Temperature (°C)",
            value=float(st.session_state.live_temp),
            disabled=True
        )
        humidity = st.sidebar.number_input(
            "Humidity (%)",
            value=float(st.session_state.live_humidity),
            disabled=True
        )
        rainfall = st.sidebar.number_input(
            "Estimated Seasonal Rain (mm)",
            value=float(st.session_state.live_rainfall),
            disabled=True
        )
    
    else:
        # Manual entry
        temperature = st.sidebar.slider("Temperature (°C)", 0.0, 50.0, 25.0)
        humidity = st.sidebar.slider("Humidity (%)", 0.0, 100.0, 60.0)
        rainfall = st.sidebar.slider("Rainfall (mm)", 0.0, 2000.0, 100.0)
    
    # --- Sidebar: Soil Data ---
    st.sidebar.header("🌱 Soil Parameters")
    N = st.sidebar.number_input("Nitrogen (N) ppm", 0, 200, 50)
    P = st.sidebar.number_input("Phosphorus (P) ppm", 0, 200, 50)
    K = st.sidebar.number_input("Potassium (K) ppm", 0, 200, 50)
    ph = st.sidebar.slider("Soil pH", 0.0, 14.0, 6.5)
    
    # --- Main Content: Crop Recommendation ---
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌱 Recommend Crop", use_container_width=True):
            with st.spinner("Analyzing conditions..."):
                data = {
                    "N": N,
                    "P": P,
                    "K": K,
                    "temperature": temperature,
                    "humidity": humidity,
                    "ph": ph,
                    "rainfall": rainfall
                }
                
                result = get_crop_recommendation(data)
                
                if result and "first_crop" in result:
                    st.session_state.first_crop = result["first_crop"]
                    st.session_state.second_crop = result["second_crop"]
                    st.session_state.first_confidence = result.get("confidence_first", 0)
                    st.session_state.second_confidence = result.get("confidence_second", 0)
                    
                    st.success("✅ Recommendations Generated")
                    st.metric(
                        "Top Recommended Crop",
                        result["first_crop"].title(),
                        f"Confidence: {result.get('confidence_first', 0):.2%}"
                    )
                    st.metric(
                        "Alternative Crop",
                        result["second_crop"].title(),
                        f"Confidence: {result.get('confidence_second', 0):.2%}"
                    )
                elif result is None:
                    st.error("❌ Failed to get recommendations. Check the error message above.")
                else:
                    st.error(f"❌ Unexpected response from API: {result}")
    
    # --- Main Content: Yield Prediction ---
    with col2:
        if st.button("📈 Predict Yield", use_container_width=True):
            if "first_crop" not in st.session_state:
                st.error("Please recommend crops first!")
            else:
                with st.spinner("Calculating yields..."):
                    crops = [
                        st.session_state.first_crop,
                        st.session_state.second_crop
                    ]
                    
                    st.success("✅ Yield Predictions")
                    
                    for crop in crops:
                        data = {
                            "Crop": crop,              # Capitalized 'Crop'
                            "Avg_Nitrogen": N,         # Matched to backend expectation
                            "Avg_Phosphorous": P,      # Matched to backend expectation
                            "Avg_Potassium": K,        # Matched to backend expectation
                            "temperature": temperature, 
                            "humidity": humidity,
                            "pH": ph,                  # Capitalized 'pH'
                            "rainfall": rainfall
                        }
                        
                        result = predict_yield(data)
                        if result and "yield" in result:
                            st.metric(
                                f"📊 Estimated Yield - {crop.title()}",
                                f"{result['yield']:.2f} tons/ha"
                            )
    
    # --- Model Performance Metrics ---
    st.divider()
    st.subheader("📊 Model Performance")
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Crop Recommendation Accuracy", "98%")
    metric_col2.metric("Yield Prediction R² Score", "0.91")
    metric_col3.metric("RMSE", "0.59 tons/ha")
    
    # --- Logout Button ---
    # --- Logout Button ---
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        
        # NEW: Clear the URL parameter
        st.query_params.clear() 
        
        st.rerun()


# ============================================
# Main Application Flow
# ============================================

if not st.session_state.logged_in:
    show_auth_page()
    st.stop()
else:
    show_main_app()