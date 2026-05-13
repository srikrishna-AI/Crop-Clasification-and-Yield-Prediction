"""
Data preprocessing pipeline for crop yield prediction
Handles feature scaling and encoding for model input
"""

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer, StandardScaler, OneHotEncoder


def log_normal_transform(x: np.ndarray) -> np.ndarray:
    """
    Apply log1p transformation to normalize data distribution
    
    Args:
        x: Input array
        
    Returns:
        Transformed array
    """
    return np.log1p(x)


def get_preprocessor() -> ColumnTransformer:
    """
    Create and return a preprocessing pipeline
    
    Applies:
    - Log-normal transformation for numerical features
    - Standard scaling for numerical features
    - One-hot encoding for categorical features
    - Standard scaling for encoded categorical features
    
    Returns:
        ColumnTransformer: Fitted preprocessor pipeline
    """
    numerical_columns = [
        "Avg_Nitrogen",
        "Avg_Phosphorous",
        "Avg_Potassium",
        "pH",
        "temperature",
        "humidity",
        "rainfall"
    ]
    
    categorical_columns = ["Crop"]

    # Pipeline for numerical features
    num_pipeline = Pipeline(
        steps=[
            ('log_normal', FunctionTransformer(log_normal_transform)),
            ("scaler", StandardScaler())
        ]
    )

    # Pipeline for categorical features
    cat_pipeline = Pipeline(
        steps=[
            ("one_hot_encoder", OneHotEncoder(sparse_output=False,
                                             handle_unknown='ignore')),
            ("scaler", StandardScaler(with_mean=False))
        ]
    )

    # Combine both pipelines
    preprocessor = ColumnTransformer(
        transformers=[
            ("num_pipeline", num_pipeline, numerical_columns),
            ("cat_pipeline", cat_pipeline, categorical_columns)
        ]
    )

    return preprocessor
