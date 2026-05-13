# ============================================
# FastAPI Application for Smart Crop Advisor
# ============================================

# 1. Standard Library Imports
from typing import Dict, List

# 2. Third-Party Framework Imports
from fastapi import FastAPI
import uvicorn
import numpy as np
import pandas as pd
import joblib

# 3. Local Imports
from config import CropRecomend, CropYield
from preprocessor import log_normal_transform

# ============================================
# Configuration & Constants
# ============================================

# Crop index to name mapping
CROP_MAPPING = {
    0: 'banana',
    1: 'coconut',
    2: 'jute',
    3: 'maize',
    4: 'rice'
}

# ============================================
# Initialize FastAPI Application
# ============================================

app = FastAPI(
    title="Smart Crop Advisor API",
    description="API for crop recommendation and yield prediction",
    version="1.0.0"
)

# ============================================
# Load Models (Global - loaded once at startup)
# ============================================

import os
import sys

# Get the directory where this script is located (src/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # Parent directory (project root)

# Model file paths
MODEL_PATHS = {
    'crop_recommendation': os.path.join(BASE_DIR, "models", "crop_recomend_model.pkl"),
    'preprocessor': os.path.join(BASE_DIR, "models", "preprocessor.pkl"),
    'scaler': os.path.join(BASE_DIR, "models", "crop_recomend_scaler.pkl"),
    'yield_prediction': os.path.join(BASE_DIR, "models", "best_RandomForest_model.pkl")
}

crop_recommendation_model = None
preprocessor = None
scaler = None
crop_yield_model = None
model_errors = []

print(f"[INFO] Base Directory: {BASE_DIR}")
print(f"[INFO] Script Directory: {SCRIPT_DIR}")

try:
    # Load crop recommendation model
    print(f"[LOADING] Crop Recommendation Model: {MODEL_PATHS['crop_recommendation']}")
    if os.path.exists(MODEL_PATHS['crop_recommendation']):
        crop_recommendation_model = joblib.load(MODEL_PATHS['crop_recommendation'])
        print(f"✓ Crop recommendation model loaded successfully")
    else:
        error_msg = f"File not found: {MODEL_PATHS['crop_recommendation']}"
        print(f"✗ {error_msg}")
        model_errors.append(error_msg)
    
    # Load preprocessor
    print(f"[LOADING] Preprocessor: {MODEL_PATHS['preprocessor']}")
    if os.path.exists(MODEL_PATHS['preprocessor']):
        preprocessor = joblib.load(MODEL_PATHS['preprocessor'])
        print(f"✓ Preprocessor loaded successfully")
    else:
        error_msg = f"File not found: {MODEL_PATHS['preprocessor']}"
        print(f"✗ {error_msg}")
        model_errors.append(error_msg)
    
    # Load scaler
    print(f"[LOADING] Scaler: {MODEL_PATHS['scaler']}")
    if os.path.exists(MODEL_PATHS['scaler']):
        scaler = joblib.load(MODEL_PATHS['scaler'])
        print(f"✓ Scaler loaded successfully")
    else:
        error_msg = f"File not found: {MODEL_PATHS['scaler']}"
        print(f"✗ {error_msg}")
        model_errors.append(error_msg)
    
    # Load yield prediction model
    print(f"[LOADING] Yield Prediction Model: {MODEL_PATHS['yield_prediction']}")
    if os.path.exists(MODEL_PATHS['yield_prediction']):
        crop_yield_model = joblib.load(MODEL_PATHS['yield_prediction'])
        print(f"✓ Yield prediction model loaded successfully")
    else:
        error_msg = f"File not found: {MODEL_PATHS['yield_prediction']}"
        print(f"✗ {error_msg}")
        model_errors.append(error_msg)
    
    # Summary
    if not model_errors:
        print("\n✓ All models loaded successfully!")
    else:
        print("\n⚠ Some models failed to load:")
        for error in model_errors:
            print(f"  - {error}")

except Exception as e:
    print(f"\n❌ Critical Error loading models: {str(e)}")
    import traceback
    traceback.print_exc()
    model_errors.append(str(e))

# ============================================
# Helper Functions
# ============================================

def get_crop_name(crop_index: int) -> str:
    """
    Convert crop index to crop name
    
    Args:
        crop_index: Integer index of the crop
        
    Returns:
        str: Name of the crop
    """
    return CROP_MAPPING.get(crop_index, 'none')


# ============================================
# API Endpoints
# ============================================

@app.get('/')
def index():
    """Root endpoint - Health check"""
    return {
        'message': 'Karshak Siksha - Smart Crop Advisor API',
        'status': 'running'
    }


@app.post('/recomendCrop')
def get_crop_recommendation(data: CropRecomend):
    """
    Get crop recommendations based on soil and weather conditions
    
    Args:
        data: CropRecomend object with N, P, K, temperature, humidity, pH, rainfall
        
    Returns:
        dict: Top two recommended crops with confidence scores
    """
    if crop_recommendation_model is None:
        error_msg = "\n".join(model_errors) if model_errors else "Crop recommendation model not loaded"
        return {
            'error': True,
            'message': error_msg,
            'first_crop': 'error',
            'second_crop': 'error',
            'confidence_first': 0.0,
            'confidence_second': 0.0
        }
    
    try:
        # Extract input features
        features = [[
            data.N, data.P, data.K,
            data.temperature, data.humidity,
            data.ph, data.rainfall
        ]]
        
        # Predict probabilities for all crops
        probabilities = crop_recommendation_model.predict_proba(features)
        
        # Get indices of top two probabilities
        top_two_indices = np.argsort(probabilities[0])[-2:][::-1]
        
        # Map indices to crop names
        first_crop = get_crop_name(top_two_indices[0])
        second_crop = get_crop_name(top_two_indices[1])
        
        return {
            'error': False,
            'first_crop': first_crop,
            'second_crop': second_crop,
            'confidence_first': float(probabilities[0][top_two_indices[0]]),
            'confidence_second': float(probabilities[0][top_two_indices[1]])
        }
    except Exception as e:
        print(f"Error in crop recommendation: {e}")
        return {
            'error': True,
            'message': f"Error during prediction: {str(e)}",
            'first_crop': 'error',
            'second_crop': 'error',
            'confidence_first': 0.0,
            'confidence_second': 0.0
        }


@app.post("/yieldPrediction")
def predict_yield(data: CropYield):
    """
    Predict crop yield based on soil and weather conditions
    
    Args:
        data: CropYield object with crop type and environmental features
        
    Returns:
        dict: Predicted yield in tons/hectare
    """
    if preprocessor is None or crop_yield_model is None:
        error_msg = "\n".join(model_errors) if model_errors else "Models not loaded"
        return {
            'error': True,
            'message': error_msg,
            'yield': 0.0,
            'unit': 'tons/hectare'
        }
    
    try:
        # Create DataFrame for preprocessing
        df = pd.DataFrame([{
            "Crop": data.Crop,
            "Avg_Nitrogen": data.Avg_Nitrogen,
            "Avg_Phosphorous": data.Avg_Phosphorous,
            "Avg_Potassium": data.Avg_Potassium,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "pH": data.pH,
            "rainfall": data.rainfall
        }])
        
        # Preprocess and predict
        X = preprocessor.transform(df)
        prediction = crop_yield_model.predict(X)[0]
        
        return {
            'error': False,
            'yield': float(prediction),
            'unit': 'tons/hectare'
        }
    except Exception as e:
        print(f"Error in yield prediction: {e}")
        return {
            'error': True,
            'message': f"Error during prediction: {str(e)}",
            'yield': 0.0,
            'unit': 'tons/hectare'
        }


# ============================================
# Application Entry Point
# ============================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)