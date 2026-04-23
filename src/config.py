"""
Configuration models for Smart Crop Advisor
Contains Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field


class CropRecomend(BaseModel):
    """Schema for crop recommendation request"""
    N: float = Field(..., description="Nitrogen content")
    P: float = Field(..., description="Phosphorus content")
    K: float = Field(..., description="Potassium content")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Humidity percentage")
    ph: float = Field(..., description="Soil pH level")
    rainfall: float = Field(..., description="Rainfall in mm")


class CropYield(BaseModel):
    """Schema for crop yield prediction request"""
    Crop: str = Field(..., description="Crop type")
    Avg_Nitrogen: float = Field(..., description="Average Nitrogen content")
    Avg_Phosphorous: float = Field(..., description="Average Phosphorus content")
    Avg_Potassium: float = Field(..., description="Average Potassium content")
    pH: float = Field(..., description="Soil pH level")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Humidity percentage")
    rainfall: float = Field(..., description="Rainfall in mm")
