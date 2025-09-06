import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import motor.motor_asyncio
from decimal import Decimal
import uuid

from ..config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PortfolioManager:
    """Manage portfolio, positions, and budget allocation"""
    
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.collections = {}
        self.balance = Decimal(str(config.max_budget))
        self.reserved_balance = Decimal('0')
        
    async def initialize(self):
        """Initialize portfolio database"""
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(config.mongodb_uri)
        self.db = self.mongo_client.csfloat_flipper
        
        self.collections = {
            'positions': self.db.positions,
            'transactions': self.db.transactions,
            'portfolio_history': self.db.portfolio_history,
            'balance_history': self.db.balance_history
        }
        
        # Create indexes
        await self._create_indexes()
        
        # Load current balance
        await self._load_balance()
        
        # Start portfolio tracking
        asyncio.create_task(self._track_portfolio_value())
        
        logger.info(f"Portfolio initialized with balance: ${self.balance}")
        
    async def _create_indexes(self):
        """Create portfolio indexes"""
        await self.collections['positions'].create_index('status')
        await self.collections['positions'].create_index('open_time')
        await self.collections['positions'].create_index('listing_id', unique=True)
        
        await self.collections['transactions'].create_index('timestamp')
        await self.collections['transactions'].create_index('type')
        
    async def _load_balance(self):
        """Load current balance from database"""
        latest_balance = await self.collections['balance_history'].find_one(
            sort=[('timestamp', -1)]
        )
        
        if latest_balance:
            self.balance = Decimal(str(latest_balance['balance']))
            self.reserved_balance = Decimal(str(latest_balance.get('reserved', 0)))
        else:
            # Initialize balance
            await self._update_balance_history()
            
    async def open_position(self, listing_data: Dict, strategy: str) -> Optional[str]:
        """Open a new position"""
        position_id = str(uuid.uuid4())
        buy_price = Decimal(str(listing_data['price']))
        
        # Check available balance
        if not await self.reserve_funds(buy_price):
            logger.warning("Insufficient balance for position")
            return None
            
        position = {
            '_id': position_id,
            'listing_id': listing_data['id'],
            'market_hash_name': listing_data['market_hash_name'],
            'buy_price': float(buy_price),
            'current_price': float(buy_price),
            'quantity': 1,
            'status': 'open',
            'strategy': strategy,
            'open_time': datetime.utcnow(),
            'item_data': listing_data,
            'profit': 0,
            'profit_percentage': 0,
            'fees_paid': float(buy_price * Decimal('0.065'))  # Estimated fees
        }
        
        await self.collections['positions'].insert_one(position)
        
        # Record transaction
        await self._record_transaction({
            'type': 'buy',
            'position_id': position_id,
            'amount': float(buy_price),
            'item': listing_data['market_hash_name'],
            'strategy': strategy
        })
        
        logger.info(f"Opened position {position_id} for ${buy_price}")
        return position_id
        
    async def close_position(self, position_id: str, sell_price: float, 
                           reason: str = 'manual') -> Dict:
        """Close a position"""
        position = await self.collections['positions'].find_one({'_id': position_id})
        
        if not position or position['status'] != 'open':
            raise ValueError(f"Invalid position: {position_id}")
            
        sell_price = Decimal(str(sell_price))
        buy_price = Decimal(str(position['buy_price']))
        
        # Calculate profit
        sell_fees = sell_price * Decimal('0.065')
        net_profit = sell_price - buy_price - Decimal(str(position['fees_paid'])) - sell_fees
        profit_percentage = (net_profit / buy_price) * 100
        
        # Update position
        update_data = {
            'status': 'closed',
            'close_time': datetime.utcnow(),
            'sell_price': float(sell_price),
            'profit': float(net_profit),
            'profit_percentage': float(profit_percentage),
            'close_reason': reason,
            'hold_time': (datetime.utcnow() - position['open_time']).total_seconds()
        }
        
        await self.collections['positions'].update_one(
            {'_id': position_id},
            {'$set': update_data}
        )
        
        # Release reserved funds and update balance
        await self.release_funds(buy_price)
        self.balance += net_profit
        await self._update_balance_history()
        
        # Record transaction
        await self._record_transaction({
            'type': 'sell',
            'position_id': position_id,
            'amount': float(sell_price),
            'profit': float(net_profit),
            'item': position['market_hash_name'],
            'strategy': position['strategy']
        })
        
        logger.info(f"Closed position {position_id} - Profit: ${net_profit:.2f} ({profit_percentage:.1f}%)")
        
        return {
            'position_id': position_id,
            'profit': float(net_profit),
            'profit_percentage': float(profit_percentage),
            'hold_time': update_data['hold_time']
        }
        
    async def update_position_price(self, position_id: str, current_price: float):
        """Update current price of a position"""
        position = await self.collections['positions'].find_one({'_id': position_id})
        
        if not position or position['status'] != 'open':
            return
            
        current_price = Decimal(str(current_price))
        buy_price = Decimal(str(position['buy_price']))
        
        # Calculate unrealized profit
        sell_fees = current_price * Decimal('0.065')
        unrealized_profit = current_price - buy_price - Decimal(str(position['fees_paid'])) - sell_fees
        profit_percentage = (unrealized_profit / buy_price) * 100
        
        await self.collections['positions'].update_one(
            {'_id': position_id},
            {'$set': {
                'current_price': float(current_price),
                'unrealized_profit': float(unrealized_profit),
                'profit_percentage': float(profit_percentage),
                'last_updated': datetime.utcnow()
            }}
        )
        
    async def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        positions = await self.collections['positions'].find({
            'status': 'open'
        }).to_list(None)
        
        return positions
        
    async def get_position_by_listing(self, listing_id: str) -> Optional[Dict]:
        """Get position by listing ID"""
        return await self.collections['positions'].find_one({
            'listing_id': listing_id
        })
        
    async def reserve_funds(self, amount: Decimal) -> bool:
        """Reserve funds for a trade"""
        if self.balance - self.reserved_balance >= amount:
            self.reserved_balance += amount
            return True
        return False
        
    async def release_funds(self, amount: Decimal):
        """Release reserved funds"""
        self.reserved_balance = max(Decimal('0'), self.reserved_balance - amount)
        
    async def get_available_budget(self) -> float:
        """Get available budget for trading"""
        return float(self.balance - self.reserved_balance)
        
    async def get_portfolio_value(self) -> Dict:
        """Calculate total portfolio value"""
        positions = await self.get_open_positions()
        
        total_invested = sum(p['buy_price'] for p in positions)
        total_current_value = sum(p.get('current_price', p['buy_price']) for p in positions)
        
        return {
            'cash_balance': float(self.balance),
            'reserved_balance': float(self.reserved_balance),
            'available_balance': float(self.balance - self.reserved_balance),
            'positions_value': total_current_value,
            'total_invested': total_invested,
            'total_value': float(self.balance) + total_current_value,
            'unrealized_profit': total_current_value - total_invested,
            'positions_count': len(positions)
        }
        
    async def _record_transaction(self, transaction: Dict):
        """Record a transaction"""
        transaction['timestamp'] = datetime.utcnow()
        transaction['balance_after'] = float(self.balance)
        
        await self.collections['transactions'].insert_one(transaction)
        
    async def _update_balance_history(self):
        """Update balance history"""
        await self.collections['balance_history'].insert_one({
            'timestamp': datetime.utcnow(),
            'balance': float(self.balance),
            'reserved': float(self.reserved_balance),
            'available': float(self.balance - self.reserved_balance)
        })
        
    async def _track_portfolio_value(self):
        """Track portfolio value over time"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            
            try:
                portfolio_value = await self.get_portfolio_value()
                
                await self.collections['portfolio_history'].insert_one({
                    'timestamp': datetime.utcnow(),
                    **portfolio_value
                })
                
                # Check for stop loss
                if portfolio_value['total_value'] < float(config.max_budget) * (1 - config.max_daily_loss):
                    logger.warning("Daily loss limit reached - pausing trading")
                    # Implement trading pause logic
                    
            except Exception as e:
                logger.error(f"Portfolio tracking error: {e}")
                
    async def get_performance_stats(self, days: int = 30) -> Dict:
        """Get portfolio performance statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get closed positions
        positions = await self.collections['positions'].find({
            'status': 'closed',
            'close_time': {'$gte': start_date}
        }).to_list(None)
        
        if not positions:
            return {
                'total_trades': 0,
                'profitable_trades': 0,
                'success_rate': 0,
                'total_profit': 0,
                'avg_profit': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'avg_hold_time': 0
            }
            
        profitable = [p for p in positions if p['profit'] > 0]
        profits = [p['profit'] for p in positions]
        
        return {
            'total_trades': len(positions),
            'profitable_trades': len(profitable),
            'success_rate': len(profitable) / len(positions),
            'total_profit': sum(profits),
            'avg_profit': sum(profits) / len(profits),
            'best_trade': max(profits),
            'worst_trade': min(profits),
            'avg_hold_time': sum(p['hold_time'] for p in positions) / len(positions),
            'roi': sum(profits) / sum(p['buy_price'] for p in positions)
        }
        
    async def get_strategy_performance(self) -> Dict[str, Dict]:
        """Get performance by strategy"""
        pipeline = [
            {'$match': {'status': 'closed'}},
            {'$group': {
                '_id': '$strategy',
                'total_trades': {'$sum': 1},
                'total_profit': {'$sum': '$profit'},
                'avg_profit': {'$avg': '$profit'},
                'success_count': {
                    '$sum': {'$cond': [{'$gt': ['$profit', 0]}, 1, 0]}
                }
            }}
        ]
        
        results = await self.collections['positions'].aggregate(pipeline).to_list(None)
        
        strategy_stats = {}
        for result in results:
            strategy = result['_id']
            strategy_stats[strategy] = {
                'total_trades': result['total_trades'],
                'total_profit': result['total_profit'],
                'avg_profit': result['avg_profit'],
                'success_rate': result['success_count'] / result['total_trades']
            }
            
        return strategy_stats
        
    async def cleanup_old_positions(self, days: int = 7):
        """Clean up old positions that are stuck"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_positions = await self.collections['positions'].find({
            'status': 'open',
            'open_time': {'$lt': cutoff_date}
        }).to_list(None)
        
        for position in old_positions:
            logger.warning(f"Auto-closing old position: {position['_id']}")
            
            # Close at current price or small loss
            current_price = position.get('current_price', position['buy_price'] * 0.95)
            await self.close_position(
                position['_id'],
                current_price,
                reason='timeout'
            )
            
    async def close(self):
        """Close database connections"""
        if self.mongo_client:
            self.mongo_client.close()