"""Time-series scaler that prevents information leakage.

Uses rolling/expanding windows instead of fitting on entire dataset.
This prevents the model from "seeing the future" during training.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union
from sklearn.preprocessing import StandardScaler, MinMaxScaler


class TimeSeriesScaler:
    """
    Scaler for time-series data that prevents information leakage.
    
    Instead of using fit_transform() on the entire dataset (which leaks future
    information), this uses rolling or expanding windows.
    """
    
    def __init__(
        self,
        method: str = "rolling",  # 'rolling' or 'expanding'
        window_size: int = 252,  # 1 year of trading days
        scaler_type: str = "standard",  # 'standard' or 'minmax'
    ):
        """
        Initialize time-series scaler.
        
        Args:
            method: 'rolling' (fixed window) or 'expanding' (all past data)
            window_size: Size of rolling window (ignored for expanding)
            scaler_type: Type of scaler ('standard' or 'minmax')
        """
        self.method = method
        self.window_size = window_size
        self.scaler_type = scaler_type
        
        if scaler_type == "standard":
            self.base_scaler = StandardScaler()
        elif scaler_type == "minmax":
            self.base_scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unknown scaler_type: {scaler_type}")
    
    def fit_transform_rolling(
        self,
        data: Union[pd.DataFrame, pd.Series],
        min_periods: int = 1
    ) -> Union[pd.DataFrame, pd.Series]:
        """
        Scale data using rolling window (prevents information leakage).
        
        For each point, only uses data from the past (within window).
        
        Args:
            data: DataFrame or Series to scale
            min_periods: Minimum periods required for scaling
        
        Returns:
            Scaled data
        """
        if isinstance(data, pd.Series):
            data = data.to_frame()
            was_series = True
        else:
            was_series = False
        
        scaled_data = data.copy()
        
        for col in data.columns:
            for i in range(len(data)):
                # Determine window
                if self.method == "rolling":
                    window_start = max(0, i - self.window_size + 1)
                else:  # expanding
                    window_start = 0
                
                window_end = i + 1
                window_data = data[col].iloc[window_start:window_end]
                
                if len(window_data) < min_periods:
                    # Not enough data, use raw value or skip
                    scaled_data.iloc[i, data.columns.get_loc(col)] = data.iloc[i, data.columns.get_loc(col)]
                    continue
                
                # Calculate statistics from window only
                mean = window_data.mean()
                std = window_data.std()
                
                # Avoid division by zero
                if std == 0 or pd.isna(std):
                    std = 1.0
                
                # Scale current value
                if self.scaler_type == "standard":
                    scaled_value = (data.iloc[i, data.columns.get_loc(col)] - mean) / std
                else:  # minmax
                    min_val = window_data.min()
                    max_val = window_data.max()
                    if max_val == min_val:
                        scaled_value = 0.0
                    else:
                        scaled_value = (data.iloc[i, data.columns.get_loc(col)] - min_val) / (max_val - min_val)
                
                scaled_data.iloc[i, data.columns.get_loc(col)] = scaled_value
        
        if was_series:
            return scaled_data.iloc[:, 0]
        return scaled_data
    
    def transform(
        self,
        data: Union[pd.DataFrame, pd.Series],
        reference_data: Optional[Union[pd.DataFrame, pd.Series]] = None
    ) -> Union[pd.DataFrame, pd.Series]:
        """
        Transform new data using statistics from reference data.
        
        Args:
            data: Data to transform
            reference_data: Reference data for statistics (if None, uses data itself)
        
        Returns:
            Transformed data
        """
        if reference_data is None:
            reference_data = data
        
        if isinstance(data, pd.Series):
            data = data.to_frame()
            was_series = True
        else:
            was_series = False
        
        if isinstance(reference_data, pd.Series):
            reference_data = reference_data.to_frame()
        
        # Use statistics from reference data
        if self.scaler_type == "standard":
            mean = reference_data.mean()
            std = reference_data.std().replace(0, 1)
            scaled = (data - mean) / std
        else:  # minmax
            min_val = reference_data.min()
            max_val = reference_data.max()
            scaled = (data - min_val) / (max_val - min_val).replace(0, 1)
        
        if was_series:
            return scaled.iloc[:, 0]
        return scaled
