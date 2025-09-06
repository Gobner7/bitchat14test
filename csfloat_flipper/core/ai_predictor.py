import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import tensorflow as tf
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import joblib
from datetime import datetime, timedelta
import asyncio
from collections import deque
import pickle

from ..config import config
from ..utils.logger import get_logger
from ..database.market_data import MarketDataStore

logger = get_logger(__name__)

class AdvancedAIPredictor:
    """Revolutionary AI-powered price prediction with multiple ML models"""
    
    def __init__(self, market_data_store: MarketDataStore):
        self.market_data = market_data_store
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.prediction_cache = {}
        self.performance_metrics = deque(maxlen=1000)
        
        # Initialize models
        self._initialize_models()
        
        # Start background training
        asyncio.create_task(self._continuous_learning())
        
    def _initialize_models(self):
        """Initialize multiple ML models for ensemble prediction"""
        
        # Deep Neural Network for complex patterns
        self.models['dnn'] = self._build_dnn_model()
        
        # LSTM for time series prediction
        self.models['lstm'] = self._build_lstm_model()
        
        # Random Forest for feature importance
        self.models['rf'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=20,
            n_jobs=-1,
            random_state=42
        )
        
        # Gradient Boosting for high accuracy
        self.models['gb'] = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=10,
            random_state=42
        )
        
        # Initialize scalers
        self.scalers['features'] = StandardScaler()
        self.scalers['target'] = MinMaxScaler()
        
    def _build_dnn_model(self) -> tf.keras.Model:
        """Build deep neural network with advanced architecture"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(512, activation='relu', input_shape=(150,)),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.3),
            
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.2),
            
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.2),
            
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='linear')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='huber',
            metrics=['mae', 'mse']
        )
        
        return model
        
    def _build_lstm_model(self) -> tf.keras.Model:
        """Build LSTM model for time series prediction"""
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(128, return_sequences=True, input_shape=(30, 50)),
            tf.keras.layers.Dropout(0.2),
            
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dropout(0.2),
            
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='linear')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
        
    async def predict_price(self, item_data: Dict) -> Dict[str, float]:
        """Predict item price using ensemble of models"""
        try:
            # Extract features
            features = await self._extract_features(item_data)
            
            # Check cache
            cache_key = self._generate_cache_key(item_data)
            if cache_key in self.prediction_cache:
                cached = self.prediction_cache[cache_key]
                if (datetime.now() - cached['timestamp']).seconds < 300:  # 5 min cache
                    return cached['predictions']
            
            predictions = {}
            
            # Get predictions from each model
            if hasattr(self.models['dnn'], 'predict'):
                dnn_pred = self.models['dnn'].predict(features['dnn'], verbose=0)[0][0]
                predictions['dnn'] = float(dnn_pred)
            
            if hasattr(self.models['lstm'], 'predict'):
                lstm_pred = self.models['lstm'].predict(features['lstm'], verbose=0)[0][0]
                predictions['lstm'] = float(lstm_pred)
            
            if hasattr(self.models['rf'], 'predict'):
                rf_pred = self.models['rf'].predict(features['standard'])[0]
                predictions['rf'] = float(rf_pred)
            
            if hasattr(self.models['gb'], 'predict'):
                gb_pred = self.models['gb'].predict(features['standard'])[0]
                predictions['gb'] = float(gb_pred)
            
            # Ensemble prediction with weighted average
            weights = {'dnn': 0.3, 'lstm': 0.25, 'rf': 0.25, 'gb': 0.2}
            ensemble_pred = sum(predictions.get(k, 0) * v for k, v in weights.items())
            
            # Calculate confidence based on model agreement
            if predictions:
                std_dev = np.std(list(predictions.values()))
                confidence = 1 - (std_dev / ensemble_pred) if ensemble_pred > 0 else 0
            else:
                confidence = 0
            
            result = {
                'predicted_price': ensemble_pred,
                'confidence': confidence,
                'model_predictions': predictions,
                'price_range': {
                    'min': ensemble_pred * 0.95,
                    'max': ensemble_pred * 1.05
                }
            }
            
            # Cache result
            self.prediction_cache[cache_key] = {
                'predictions': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'predicted_price': item_data.get('price', 0),
                'confidence': 0,
                'model_predictions': {},
                'price_range': {'min': 0, 'max': 0}
            }
            
    async def _extract_features(self, item_data: Dict) -> Dict[str, np.ndarray]:
        """Extract advanced features for ML models"""
        features = {
            # Basic features
            'price': item_data.get('price', 0),
            'float_value': item_data.get('float_value', 0),
            'pattern_index': item_data.get('pattern_index', -1),
            'stattrak': int(item_data.get('stattrak', False)),
            'souvenir': int(item_data.get('souvenir', False)),
            
            # Advanced features
            'wear_category': self._get_wear_category(item_data.get('float_value', 0)),
            'rarity_score': await self._calculate_rarity_score(item_data),
            'market_trend': await self._get_market_trend(item_data),
            'liquidity_score': await self._calculate_liquidity(item_data),
            'sticker_value': self._calculate_sticker_value(item_data.get('stickers', [])),
            
            # Time-based features
            'hour_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'days_since_release': self._days_since_release(item_data),
            
            # Pattern-specific features
            'pattern_rarity': await self._get_pattern_rarity(item_data),
            'pattern_demand': await self._get_pattern_demand(item_data),
            
            # Market dynamics
            'current_supply': await self._get_current_supply(item_data),
            'demand_index': await self._get_demand_index(item_data),
            'price_volatility': await self._calculate_volatility(item_data),
            
            # Cross-market features
            'steam_price': item_data.get('steam_price', 0),
            'buff_price': item_data.get('buff_price', 0),
            'price_differential': self._calculate_price_differential(item_data),
        }
        
        # Add historical features
        historical = await self._get_historical_features(item_data)
        features.update(historical)
        
        # Prepare features for different models
        standard_features = np.array(list(features.values())).reshape(1, -1)
        
        # Prepare time series features for LSTM
        time_series = await self._prepare_time_series(item_data)
        
        # Prepare features for DNN (includes engineered features)
        dnn_features = self._engineer_features(features)
        
        return {
            'standard': standard_features,
            'lstm': time_series,
            'dnn': dnn_features
        }
        
    def _get_wear_category(self, float_value: float) -> int:
        """Convert float to wear category"""
        if float_value < 0.07:
            return 0  # Factory New
        elif float_value < 0.15:
            return 1  # Minimal Wear
        elif float_value < 0.38:
            return 2  # Field-Tested
        elif float_value < 0.45:
            return 3  # Well-Worn
        else:
            return 4  # Battle-Scarred
            
    async def _calculate_rarity_score(self, item_data: Dict) -> float:
        """Calculate item rarity score"""
        # Implement complex rarity calculation
        base_rarity = 1.0
        
        # Float rarity
        float_value = item_data.get('float_value', 0.5)
        if float_value < 0.001 or float_value > 0.999:
            base_rarity *= 10
        elif float_value < 0.01 or float_value > 0.99:
            base_rarity *= 5
            
        # Pattern rarity
        pattern_index = item_data.get('pattern_index', -1)
        if pattern_index in [661, 670, 321, 387]:  # Rare patterns
            base_rarity *= 8
            
        return min(base_rarity, 100)
        
    async def _get_market_trend(self, item_data: Dict) -> float:
        """Get current market trend for item"""
        # Query historical data
        history = await self.market_data.get_price_history(
            item_data.get('market_hash_name', ''),
            days=7
        )
        
        if len(history) < 2:
            return 0
            
        # Calculate trend
        prices = [h['price'] for h in history]
        trend = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        
        return trend
        
    def _calculate_sticker_value(self, stickers: List[Dict]) -> float:
        """Calculate total sticker value"""
        total_value = 0
        
        for sticker in stickers:
            value = sticker.get('price', 0)
            wear = sticker.get('wear', 0)
            
            # Adjust for wear
            if wear < 0.1:
                value *= 0.9
            elif wear < 0.25:
                value *= 0.7
            elif wear < 0.5:
                value *= 0.5
            else:
                value *= 0.3
                
            total_value += value
            
        return total_value
        
    async def _continuous_learning(self):
        """Continuously update models with new data"""
        while True:
            try:
                await asyncio.sleep(config.model_update_interval)
                
                # Get recent trades
                recent_data = await self.market_data.get_recent_trades(
                    hours=24,
                    limit=10000
                )
                
                if len(recent_data) > 100:
                    # Prepare training data
                    X, y = await self._prepare_training_data(recent_data)
                    
                    # Update models
                    await self._update_models(X, y)
                    
                    logger.info("Models updated with recent market data")
                    
            except Exception as e:
                logger.error(f"Continuous learning error: {e}")
                
    async def _prepare_training_data(self, trades: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from recent trades"""
        X = []
        y = []
        
        for trade in trades:
            features = await self._extract_features(trade)
            X.append(features['standard'].flatten())
            y.append(trade.get('sold_price', 0))
            
        return np.array(X), np.array(y)
        
    async def _update_models(self, X: np.ndarray, y: np.ndarray):
        """Update models with new data"""
        # Scale features
        X_scaled = self.scalers['features'].fit_transform(X)
        y_scaled = self.scalers['target'].fit_transform(y.reshape(-1, 1))
        
        # Update sklearn models
        self.models['rf'].fit(X_scaled, y_scaled.ravel())
        self.models['gb'].fit(X_scaled, y_scaled.ravel())
        
        # Fine-tune neural networks
        self.models['dnn'].fit(
            X_scaled, y_scaled,
            epochs=5,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
    def _engineer_features(self, features: Dict) -> np.ndarray:
        """Engineer additional features for DNN"""
        engineered = list(features.values())
        
        # Add polynomial features
        for i in range(len(features)):
            for j in range(i+1, min(i+5, len(features))):
                engineered.append(list(features.values())[i] * list(features.values())[j])
                
        # Add ratios
        if features['price'] > 0:
            engineered.append(features['sticker_value'] / features['price'])
            engineered.append(features['steam_price'] / features['price'])
            
        return np.array(engineered).reshape(1, -1)
        
    async def _prepare_time_series(self, item_data: Dict) -> np.ndarray:
        """Prepare time series data for LSTM"""
        # Get historical data
        history = await self.market_data.get_price_history(
            item_data.get('market_hash_name', ''),
            days=30
        )
        
        if len(history) < 30:
            # Pad with zeros if not enough history
            history = [{'price': 0, 'volume': 0}] * (30 - len(history)) + history
            
        # Extract time series features
        time_series = []
        for h in history:
            time_series.append([
                h.get('price', 0),
                h.get('volume', 0),
                h.get('listings', 0),
                h.get('sales', 0),
                # Add more time series features
            ])
            
        return np.array(time_series).reshape(1, 30, -1)
        
    def _generate_cache_key(self, item_data: Dict) -> str:
        """Generate cache key for predictions"""
        key_parts = [
            item_data.get('market_hash_name', ''),
            str(item_data.get('float_value', 0)),
            str(item_data.get('pattern_index', -1)),
            str(item_data.get('stattrak', False))
        ]
        return '_'.join(key_parts)
        
    async def get_profit_probability(self, buy_price: float, predicted_price: float) -> float:
        """Calculate probability of profitable trade"""
        if buy_price <= 0:
            return 0
            
        profit_margin = (predicted_price - buy_price) / buy_price
        
        # Use historical data to calculate probability
        similar_trades = await self.market_data.get_similar_trades(
            profit_margin=profit_margin,
            limit=1000
        )
        
        if similar_trades:
            successful = sum(1 for t in similar_trades if t['profitable'])
            return successful / len(similar_trades)
        
        # Fallback calculation based on margin
        if profit_margin > 0.3:
            return 0.9
        elif profit_margin > 0.2:
            return 0.8
        elif profit_margin > 0.1:
            return 0.6
        else:
            return 0.3