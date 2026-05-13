"""
Advanced FastAPI endpoints for Smart Crop Advisor
Includes detailed recommendations with explainability features
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

try:
    import shap
except ImportError:
    shap = None

import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Smart Crop Advisor Advanced API",
    description="Advanced API with explainability features",
    version="1.0"
)

# ============================================
# Model and Data Loading
# ============================================

MODEL_PATH = "../models/crop_recommendation_model.pkl"
DATA_PATH = "../data/processed/Extracted Data/Updated_CropRecomendation.csv"

model = None
data = None

try:
    model = joblib.load(MODEL_PATH)
    data = pd.read_csv(DATA_PATH)
    logger.info("Models and data loaded successfully")
except Exception as e:
    logger.error(f"Error loading models/data: {e}")
    model = None
    data = None

# ============================================
# Pydantic Models for Request/Response
# ============================================

class RecommendationRequest(BaseModel):
    """Request schema for state-based recommendations"""
    state: str = Field(..., description="State name")
    season: str = Field(..., description="Season name")


class FeatureContribution(BaseModel):
    """Feature contribution to model prediction"""
    feature: str = Field(..., description="Feature name")
    value: Any = Field(..., description="Feature value")
    importance: float = Field(..., description="Feature importance score")


class Recommendation(BaseModel):
    """Single crop recommendation"""
    crop: str = Field(..., description="Crop name")
    suitability_score: float = Field(..., description="Score 0-1")
    predicted_yield: float = Field(..., description="Predicted yield")
    risk_indicators: Dict[str, str] = Field(..., description="Risk factors")
    top_contributing_features: List[FeatureContribution] = Field(..., description="Top 5 features")
    rationale: str = Field(..., description="Explanation for recommendation")


class RecommendationResponse(BaseModel):
    """Response with multiple recommendations"""
    recommendations: List[Recommendation] = Field(..., description="List of recommendations")
    fallback_used: bool = Field(..., description="Whether fallback data was used")
    model_version: str = Field(..., description="API version")

# ============================================
# Helper Functions
# ============================================

def get_state_data(state: str, season: str) -> pd.DataFrame:
    """
    Retrieve data for specific state and season
    
    Args:
        state: State name
        season: Season name
        
    Returns:
        DataFrame with filtered data
    """
    if data is None:
        return pd.DataFrame()
    
    df = data[(data['state'] == state) & (data['season'] == season)]
    return df


def find_nearest_state(state: str, season: str) -> Optional[str]:
    """
    Find nearest state based on climate and soil features
    
    Args:
        state: Reference state
        season: Season name
        
    Returns:
        Nearest state name or None
    """
    if data is None:
        return None
    
    try:
        feature_cols = ['rainfall', 'temperature', 'soil_ph']
        available_cols = [col for col in feature_cols if col in data.columns]
        
        if not available_cols:
            return None
        
        state_features = data[data['state'] == state][available_cols].mean()
        all_states = data['state'].unique()
        
        min_dist = float('inf')
        nearest = None
        
        for s in all_states:
            if s == state:
                continue
            s_features = data[data['state'] == s][available_cols].mean()
            dist = np.linalg.norm(state_features - s_features)
            
            if dist < min_dist:
                min_dist = dist
                nearest = s
        
        return nearest
    
    except Exception as e:
        logger.error(f"Error finding nearest state: {e}")
        return None

# ============================================
# API Endpoints
# ============================================

@app.post("/api/v1/recommend_by_state", response_model=RecommendationResponse)
def recommend_by_state(request: RecommendationRequest) -> RecommendationResponse:
    """
    Get crop recommendations based on state and season
    
    Provides detailed recommendations with risk indicators and feature importance.
    Falls back to nearest state or national average if data not available.
    
    Args:
        request: RecommendationRequest with state and season
        
    Returns:
        RecommendationResponse with recommendations and metadata
    """
    if model is None or data is None:
        raise HTTPException(status_code=500, detail="Model or data not loaded")

    df = get_state_data(request.state, request.season)
    fallback_used = False
    rationale = ""
    
    # Fallback 1: Use nearest state
    if df.empty:
        nearest_state = find_nearest_state(request.state, request.season)
        if nearest_state:
            df = get_state_data(nearest_state, request.season)
            fallback_used = True
            rationale = f"No data for {request.state}. Used nearest state: {nearest_state}."
    
    # Fallback 2: Use national average
    if df.empty:
        df = data[data['season'] == request.season]
        fallback_used = True
        rationale = f"No specific data available. Used national average."
    
    # No data available
    if df.empty:
        raise HTTPException(status_code=404, detail="No data available for recommendations")

    # Prepare features and crops
    exclude_cols = ['crop', 'state', 'season', 'yield', 'production']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_cols]
    
    crops = df['crop'].unique()
    recommendations = []
    
    # Get explainer if SHAP is available
    explainer = None
    if shap is not None:
        try:
            explainer = shap.TreeExplainer(model)
        except Exception as e:
            logger.warning(f"Could not create SHAP explainer: {e}")
    
    # Generate recommendations for each crop
    for crop in crops:
        crop_df = df[df['crop'] == crop]
        if crop_df.empty:
            continue
        
        x_input = crop_df.iloc[0][feature_cols].values.reshape(1, -1)
        
        try:
            pred_yield = float(model.predict(x_input)[0])
        except:
            pred_yield = 0.0
        
        # Calculate suitability score
        max_yield = df['yield'].max() if 'yield' in df.columns else 1.0
        suitability_score = float(pred_yield) / (max_yield + 1e-6)
        
        # Risk indicators
        rainfall = crop_df.iloc[0].get('rainfall', 0)
        risk_indicators = {
            "drought": "low" if rainfall > 800 else "high" if rainfall < 400 else "medium",
            "flood": "high" if rainfall > 2000 else "low",
            "pest": "medium"  # Placeholder
        }
        
        # Feature contributions
        top_features = []
        
        if explainer is not None:
            try:
                shap_values = explainer.shap_values(x_input)
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]
                feature_importances = np.abs(shap_values).flatten()
                top_idx = np.argsort(feature_importances)[-5:][::-1]
                
                top_features = [
                    FeatureContribution(
                        feature=feature_cols[i],
                        value=float(x_input[0][i]),
                        importance=float(feature_importances[i])
                    ) for i in top_idx if i < len(feature_cols)
                ]
            except Exception as e:
                logger.warning(f"Error computing SHAP values: {e}")
        
        recommendations.append(Recommendation(
            crop=crop,
            suitability_score=min(suitability_score, 1.0),
            predicted_yield=pred_yield,
            risk_indicators=risk_indicators,
            top_contributing_features=top_features,
            rationale=rationale or f"Recommended based on {request.state} profile."
        ))
    
    # Sort by suitability score
    recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
    
    return RecommendationResponse(
        recommendations=recommendations,
        fallback_used=fallback_used,
        model_version="v1.0"
    )
