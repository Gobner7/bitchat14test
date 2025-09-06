import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv
import json

load_dotenv()

@dataclass
class TradingConfig:
    """Advanced trading configuration with dynamic adjustments"""
    
    # API Configuration
    api_key: str = os.getenv('CSFLOAT_API_KEY', '')
    base_url: str = 'https://csfloat.com/api/v1'
    ws_url: str = 'wss://csfloat.com/ws'
    
    # Budget Management
    max_budget: float = float(os.getenv('MAX_BUDGET', '10000'))
    min_profit_margin: float = float(os.getenv('MIN_PROFIT_MARGIN', '0.15'))
    max_position_size: float = 0.2  # Max 20% of budget per item
    
    # Performance Settings
    websocket_connections: int = int(os.getenv('WEBSOCKET_CONNECTIONS', '10'))
    worker_threads: int = int(os.getenv('WORKER_THREADS', '16'))
    sniper_threads: int = int(os.getenv('SNIPER_THREADS', '32'))
    
    # Advanced Trading Parameters
    price_check_interval: float = 0.05  # 50ms ultra-fast checks
    market_depth_analysis: int = 100  # Analyze top 100 listings
    float_precision_threshold: float = 0.00001
    pattern_recognition_confidence: float = 0.85
    
    # ML Model Parameters
    prediction_window: int = 24  # hours
    training_data_days: int = 90
    model_update_interval: int = 3600  # seconds
    
    # Risk Management
    stop_loss_percentage: float = 0.05
    take_profit_percentage: float = 0.25
    max_daily_loss: float = 0.10  # 10% of budget
    position_timeout: int = 86400  # 24 hours
    
    # Stealth Features
    enable_stealth: bool = os.getenv('ENABLE_STEALTH_MODE', 'true').lower() == 'true'
    rotate_user_agents: bool = os.getenv('ROTATE_USER_AGENTS', 'true').lower() == 'true'
    request_delay_variance: float = 0.1  # ±10% random delay
    
    # Database
    mongodb_uri: str = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/csfloat_flipper')
    redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Monitoring
    enable_prometheus: bool = os.getenv('ENABLE_PROMETHEUS', 'true').lower() == 'true'
    prometheus_port: int = int(os.getenv('PROMETHEUS_PORT', '9090'))
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Advanced Strategies
    strategies: Dict[str, Dict] = {
        'pattern_arbitrage': {
            'enabled': True,
            'min_pattern_index': 0,
            'max_pattern_index': 999,
            'profit_multiplier': 1.5
        },
        'float_capping': {
            'enabled': True,
            'target_floats': [0.00, 0.07, 0.15, 0.18, 0.38, 0.45],
            'tolerance': 0.001
        },
        'sticker_value': {
            'enabled': True,
            'min_sticker_value': 50,
            'rare_sticker_multiplier': 2.0
        },
        'market_manipulation': {
            'enabled': True,
            'create_artificial_demand': True,
            'price_ladder_steps': 5
        },
        'cross_market_arbitrage': {
            'enabled': True,
            'markets': ['steam', 'buff163', 'skinport'],
            'min_arbitrage_profit': 0.10
        }
    }
    
    # Item Filters
    item_filters: Dict[str, any] = {
        'min_price': 1.0,
        'max_price': 100000.0,
        'weapon_types': ['ak47', 'awp', 'm4a1', 'knife', 'gloves'],
        'exclude_souvenir': False,
        'exclude_stattrak': False,
        'min_liquidity_score': 0.7
    }
    
    # Performance Optimizations
    use_uvloop: bool = True
    enable_jit_compilation: bool = True
    cache_ttl: int = 300  # 5 minutes
    batch_size: int = 100
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for serialization"""
        return {
            'api_key': self.api_key[:10] + '...' if self.api_key else 'Not Set',
            'max_budget': self.max_budget,
            'min_profit_margin': self.min_profit_margin,
            'strategies': self.strategies,
            'performance': {
                'websocket_connections': self.websocket_connections,
                'worker_threads': self.worker_threads,
                'sniper_threads': self.sniper_threads
            }
        }

# Global config instance
config = TradingConfig()