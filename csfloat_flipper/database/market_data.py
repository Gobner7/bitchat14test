import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING
import redis.asyncio as redis
import json
import pickle
from collections import defaultdict

from ..config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class MarketDataStore:
    """High-performance market data storage with caching"""
    
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.redis_client = None
        self.collections = {}
        
    async def initialize(self):
        """Initialize database connections"""
        # MongoDB for persistent storage
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(config.mongodb_uri)
        self.db = self.mongo_client.csfloat_flipper
        
        # Setup collections
        self.collections = {
            'listings': self.db.listings,
            'trades': self.db.trades,
            'price_history': self.db.price_history,
            'patterns': self.db.patterns,
            'market_stats': self.db.market_stats
        }
        
        # Create indexes
        await self._create_indexes()
        
        # Redis for caching
        self.redis_client = await redis.from_url(config.redis_url)
        
        logger.info("Market data store initialized")
        
    async def _create_indexes(self):
        """Create database indexes for performance"""
        # Listings indexes
        await self.collections['listings'].create_index([
            ('market_hash_name', ASCENDING),
            ('timestamp', DESCENDING)
        ])
        await self.collections['listings'].create_index([
            ('float_value', ASCENDING)
        ])
        await self.collections['listings'].create_index([
            ('pattern_index', ASCENDING)
        ])
        
        # Trades indexes
        await self.collections['trades'].create_index([
            ('timestamp', DESCENDING)
        ])
        await self.collections['trades'].create_index([
            ('profitable', ASCENDING),
            ('timestamp', DESCENDING)
        ])
        
        # Price history indexes
        await self.collections['price_history'].create_index([
            ('market_hash_name', ASCENDING),
            ('timestamp', DESCENDING)
        ])
        
    async def store_listing(self, listing: Dict):
        """Store new listing data"""
        listing['timestamp'] = datetime.utcnow()
        listing['_id'] = listing.get('id')  # Use listing ID as document ID
        
        await self.collections['listings'].replace_one(
            {'_id': listing['_id']},
            listing,
            upsert=True
        )
        
        # Update cache
        cache_key = f"listing:{listing['_id']}"
        await self.redis_client.setex(
            cache_key,
            config.cache_ttl,
            json.dumps(listing, default=str)
        )
        
    async def store_trade(self, trade: Dict):
        """Store completed trade data"""
        trade['timestamp'] = datetime.utcnow()
        
        # Calculate profitability
        if 'buy_price' in trade and 'sell_price' in trade:
            fees = (trade['buy_price'] + trade['sell_price']) * 0.065  # Avg fees
            trade['profit'] = trade['sell_price'] - trade['buy_price'] - fees
            trade['profitable'] = trade['profit'] > 0
            trade['profit_margin'] = trade['profit'] / trade['buy_price']
        
        await self.collections['trades'].insert_one(trade)
        
        # Update statistics
        await self._update_trade_statistics(trade)
        
    async def _update_trade_statistics(self, trade: Dict):
        """Update aggregated trade statistics"""
        stats_key = f"stats:{trade.get('market_hash_name', 'unknown')}"
        
        # Get current stats
        current_stats = await self.redis_client.get(stats_key)
        if current_stats:
            stats = json.loads(current_stats)
        else:
            stats = {
                'total_trades': 0,
                'profitable_trades': 0,
                'total_volume': 0,
                'avg_profit_margin': 0
            }
        
        # Update stats
        stats['total_trades'] += 1
        if trade.get('profitable'):
            stats['profitable_trades'] += 1
        stats['total_volume'] += trade.get('sell_price', 0)
        
        # Recalculate average
        if stats['total_trades'] > 0:
            stats['success_rate'] = stats['profitable_trades'] / stats['total_trades']
        
        await self.redis_client.setex(
            stats_key,
            3600,  # 1 hour cache
            json.dumps(stats)
        )
        
    async def get_price_history(self, market_hash_name: str, days: int = 30) -> List[Dict]:
        """Get price history for an item"""
        cache_key = f"price_history:{market_hash_name}:{days}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Query database
        start_date = datetime.utcnow() - timedelta(days=days)
        
        history = await self.collections['price_history'].find({
            'market_hash_name': market_hash_name,
            'timestamp': {'$gte': start_date}
        }).sort('timestamp', ASCENDING).to_list(None)
        
        # Cache result
        await self.redis_client.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps(history, default=str)
        )
        
        return history
        
    async def get_recent_trades(self, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """Get recent trades for analysis"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        trades = await self.collections['trades'].find({
            'timestamp': {'$gte': start_time}
        }).sort('timestamp', DESCENDING).limit(limit).to_list(None)
        
        return trades
        
    async def get_similar_trades(self, profit_margin: float, limit: int = 100) -> List[Dict]:
        """Get trades with similar profit margins"""
        margin_range = 0.05  # ±5%
        
        trades = await self.collections['trades'].find({
            'profit_margin': {
                '$gte': profit_margin - margin_range,
                '$lte': profit_margin + margin_range
            }
        }).limit(limit).to_list(None)
        
        return trades
        
    async def get_pattern_statistics(self, weapon_type: str) -> Dict[int, Dict]:
        """Get statistics for patterns of a weapon type"""
        cache_key = f"pattern_stats:{weapon_type}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return pickle.loads(cached)
        
        # Aggregate pattern data
        pipeline = [
            {'$match': {'weapon_type': weapon_type}},
            {'$group': {
                '_id': '$pattern_index',
                'avg_price': {'$avg': '$price'},
                'count': {'$sum': 1},
                'avg_profit': {'$avg': '$profit_margin'}
            }},
            {'$sort': {'avg_profit': -1}}
        ]
        
        results = await self.collections['trades'].aggregate(pipeline).to_list(None)
        
        pattern_stats = {
            r['_id']: {
                'avg_price': r['avg_price'],
                'count': r['count'],
                'avg_profit': r['avg_profit']
            }
            for r in results
        }
        
        # Cache result
        await self.redis_client.setex(
            cache_key,
            3600,  # 1 hour
            pickle.dumps(pattern_stats)
        )
        
        return pattern_stats
        
    async def get_float_distribution(self, market_hash_name: str) -> Dict[str, List]:
        """Get float value distribution for an item"""
        listings = await self.collections['listings'].find({
            'market_hash_name': market_hash_name
        }).to_list(1000)
        
        # Create distribution
        distribution = defaultdict(list)
        
        for listing in listings:
            float_value = listing.get('float_value', 0)
            price = listing.get('price', 0)
            
            # Categorize by wear
            if float_value < 0.07:
                category = 'factory_new'
            elif float_value < 0.15:
                category = 'minimal_wear'
            elif float_value < 0.38:
                category = 'field_tested'
            elif float_value < 0.45:
                category = 'well_worn'
            else:
                category = 'battle_scarred'
                
            distribution[category].append({
                'float': float_value,
                'price': price
            })
            
        return dict(distribution)
        
    async def update_price_snapshot(self, market_hash_name: str, price_data: Dict):
        """Update price snapshot for real-time tracking"""
        snapshot = {
            'market_hash_name': market_hash_name,
            'timestamp': datetime.utcnow(),
            'price': price_data['price'],
            'volume': price_data.get('volume', 0),
            'listings': price_data.get('listings', 0),
            'sales_24h': price_data.get('sales_24h', 0)
        }
        
        await self.collections['price_history'].insert_one(snapshot)
        
        # Update real-time cache
        rt_key = f"realtime:{market_hash_name}"
        await self.redis_client.setex(
            rt_key,
            60,  # 1 minute
            json.dumps(snapshot, default=str)
        )
        
    async def get_market_trends(self, hours: int = 24) -> Dict[str, Dict]:
        """Get market-wide trends"""
        cache_key = f"market_trends:{hours}"
        
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Calculate trends
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Most traded items
        pipeline = [
            {'$match': {'timestamp': {'$gte': start_time}}},
            {'$group': {
                '_id': '$market_hash_name',
                'count': {'$sum': 1},
                'avg_price': {'$avg': '$price'},
                'total_volume': {'$sum': '$price'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 50}
        ]
        
        most_traded = await self.collections['trades'].aggregate(pipeline).to_list(None)
        
        trends = {
            'most_traded': most_traded,
            'total_volume': sum(item['total_volume'] for item in most_traded),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache result
        await self.redis_client.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps(trends, default=str)
        )
        
        return trends
        
    async def close(self):
        """Close database connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.mongo_client:
            self.mongo_client.close()