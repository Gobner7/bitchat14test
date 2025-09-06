import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from collections import defaultdict, deque

from ..config import config
from ..utils.logger import get_logger
from ..database.portfolio import PortfolioManager

logger = get_logger(__name__)

@dataclass
class Strategy:
    """Trading strategy with performance tracking"""
    name: str
    enabled: bool
    parameters: Dict
    performance: Dict
    allocation: float  # Budget allocation percentage

class DynamicStrategyManager:
    """Advanced strategy management with ML-driven optimization"""
    
    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio = portfolio_manager
        self.strategies = self._initialize_strategies()
        self.performance_history = defaultdict(lambda: deque(maxlen=1000))
        self.budget_allocations = {}
        self.market_conditions = {}
        
        # Strategy optimization
        self.optimization_interval = 3600  # 1 hour
        self.min_sample_size = 50
        
        # Risk management
        self.max_drawdown = 0.2  # 20%
        self.risk_per_trade = 0.02  # 2% per trade
        
        # Initialize
        asyncio.create_task(self._continuous_optimization())
        asyncio.create_task(self._monitor_market_conditions())
        
    def _initialize_strategies(self) -> Dict[str, Strategy]:
        """Initialize all trading strategies"""
        strategies = {}
        
        # Pattern Arbitrage Strategy
        strategies['pattern_arbitrage'] = Strategy(
            name='Pattern Arbitrage',
            enabled=True,
            parameters={
                'target_patterns': {
                    661: {'name': 'Dragon Lore', 'multiplier': 5.0},
                    670: {'name': 'Blue Gem', 'multiplier': 4.0},
                    321: {'name': 'Fire Serpent', 'multiplier': 3.0},
                    387: {'name': 'Black Pearl', 'multiplier': 3.5},
                    179: {'name': 'Emerald', 'multiplier': 3.0},
                    555: {'name': 'Full Fade', 'multiplier': 2.5}
                },
                'min_profit': 0.25,
                'max_hold_time': 168  # hours
            },
            performance={'roi': 0, 'trades': 0, 'success_rate': 0},
            allocation=0.3
        )
        
        # Float Capping Strategy
        strategies['float_capping'] = Strategy(
            name='Float Capping',
            enabled=True,
            parameters={
                'target_ranges': [
                    {'min': 0.0000, 'max': 0.0001, 'premium': 2.0},
                    {'min': 0.0699, 'max': 0.0701, 'premium': 1.5},
                    {'min': 0.1499, 'max': 0.1501, 'premium': 1.3},
                    {'min': 0.1799, 'max': 0.1801, 'premium': 1.4},
                    {'min': 0.2499, 'max': 0.2501, 'premium': 1.2}
                ],
                'min_volume': 10,  # Min daily volume
                'max_price': 1000
            },
            performance={'roi': 0, 'trades': 0, 'success_rate': 0},
            allocation=0.25
        )
        
        # Sticker Value Strategy
        strategies['sticker_hunter'] = Strategy(
            name='Sticker Hunter',
            enabled=True,
            parameters={
                'valuable_stickers': {
                    'Katowice 2014': {'min_value': 500, 'scrape_threshold': 0.1},
                    'Crown (Foil)': {'min_value': 300, 'scrape_threshold': 0.15},
                    'iBUYPOWER Holo': {'min_value': 1000, 'scrape_threshold': 0.05},
                    'Titan Holo': {'min_value': 1500, 'scrape_threshold': 0.05}
                },
                'min_sticker_coverage': 0.8,  # 80% of gun value
                'position_multipliers': [1.0, 0.9, 0.85, 0.8]  # By position
            },
            performance={'roi': 0, 'trades': 0, 'success_rate': 0},
            allocation=0.2
        )
        
        # Market Manipulation Strategy
        strategies['market_maker'] = Strategy(
            name='Market Maker',
            enabled=True,
            parameters={
                'spread_target': 0.15,  # 15% spread
                'inventory_limit': 10,  # Max items of same type
                'price_levels': 5,  # Number of price levels
                'liquidity_provision': True,
                'wash_trading': False  # Disabled for compliance
            },
            performance={'roi': 0, 'trades': 0, 'success_rate': 0},
            allocation=0.15
        )
        
        # Cross-Market Arbitrage
        strategies['cross_market'] = Strategy(
            name='Cross Market Arbitrage',
            enabled=True,
            parameters={
                'markets': {
                    'steam': {'fee': 0.13, 'delay': 7},  # 7 day trade hold
                    'buff163': {'fee': 0.025, 'delay': 0},
                    'skinport': {'fee': 0.12, 'delay': 0},
                    'bitskins': {'fee': 0.05, 'delay': 0}
                },
                'min_arbitrage': 0.15,  # 15% minimum
                'max_exposure': 5000,  # Per market
                'execution_speed': 'instant'
            },
            performance={'roi': 0, 'trades': 0, 'success_rate': 0},
            allocation=0.1
        )
        
        # AI-Driven Momentum Strategy
        strategies['ai_momentum'] = Strategy(
            name='AI Momentum Trading',
            enabled=True,
            parameters={
                'lookback_period': 24,  # hours
                'momentum_threshold': 0.1,  # 10% price increase
                'volume_surge': 2.0,  # 2x average volume
                'exit_conditions': {
                    'profit_target': 0.25,
                    'stop_loss': 0.1,
                    'time_stop': 48  # hours
                }
            },
            performance={'roi': 0, 'trades': 0, 'success_rate': 0},
            allocation=0.0  # Dynamically allocated
        )
        
        return strategies
        
    async def get_best_strategy(self, item_data: Dict) -> Optional[Tuple[str, Dict]]:
        """Get best strategy for a specific item"""
        suitable_strategies = []
        
        for name, strategy in self.strategies.items():
            if not strategy.enabled:
                continue
                
            score = await self._evaluate_strategy_fit(name, strategy, item_data)
            if score > 0:
                suitable_strategies.append((name, score))
                
        if not suitable_strategies:
            return None
            
        # Sort by score and performance
        suitable_strategies.sort(key=lambda x: x[1] * self.strategies[x[0]].performance.get('roi', 1), reverse=True)
        
        best_strategy = suitable_strategies[0][0]
        
        # Get execution parameters
        params = await self._get_execution_parameters(best_strategy, item_data)
        
        return best_strategy, params
        
    async def _evaluate_strategy_fit(self, name: str, strategy: Strategy, item_data: Dict) -> float:
        """Evaluate how well a strategy fits an item"""
        score = 0.0
        
        if name == 'pattern_arbitrage':
            pattern = item_data.get('pattern_index', -1)
            if pattern in strategy.parameters['target_patterns']:
                score = strategy.parameters['target_patterns'][pattern]['multiplier']
                
        elif name == 'float_capping':
            float_value = item_data.get('float_value', 1)
            for range_data in strategy.parameters['target_ranges']:
                if range_data['min'] <= float_value <= range_data['max']:
                    score = range_data['premium']
                    break
                    
        elif name == 'sticker_hunter':
            sticker_value = sum(s.get('price', 0) for s in item_data.get('stickers', []))
            if sticker_value > item_data.get('price', 0) * strategy.parameters['min_sticker_coverage']:
                score = sticker_value / item_data.get('price', 1)
                
        elif name == 'cross_market':
            # Check arbitrage opportunities
            arbitrage = await self._check_arbitrage(item_data)
            if arbitrage['margin'] > strategy.parameters['min_arbitrage']:
                score = arbitrage['margin']
                
        elif name == 'ai_momentum':
            # Check momentum indicators
            momentum = await self._calculate_momentum(item_data)
            if momentum > strategy.parameters['momentum_threshold']:
                score = momentum
                
        # Adjust score based on market conditions
        score *= self._get_market_condition_multiplier(name)
        
        return score
        
    async def _get_execution_parameters(self, strategy_name: str, item_data: Dict) -> Dict:
        """Get specific execution parameters for a strategy"""
        strategy = self.strategies[strategy_name]
        params = {
            'strategy': strategy_name,
            'max_price': 0,
            'target_profit': 0,
            'hold_time': 0,
            'risk_amount': 0
        }
        
        # Calculate position size based on Kelly Criterion
        kelly_fraction = await self._calculate_kelly_criterion(strategy_name)
        available_budget = await self.portfolio.get_available_budget()
        
        # Apply strategy allocation
        strategy_budget = available_budget * strategy.allocation
        
        # Risk management
        max_risk = min(
            strategy_budget * self.risk_per_trade,
            available_budget * 0.05  # Max 5% of total
        )
        
        params['risk_amount'] = max_risk
        params['max_price'] = max_risk / (1 - strategy.parameters.get('min_profit', 0.15))
        
        # Strategy-specific parameters
        if strategy_name == 'pattern_arbitrage':
            pattern = item_data.get('pattern_index', -1)
            if pattern in strategy.parameters['target_patterns']:
                multiplier = strategy.parameters['target_patterns'][pattern]['multiplier']
                params['target_profit'] = 0.1 * multiplier
                params['hold_time'] = strategy.parameters['max_hold_time']
                
        elif strategy_name == 'float_capping':
            params['hold_time'] = 72  # 3 days for float caps
            params['target_profit'] = 0.3  # 30% for rare floats
            
        return params
        
    async def _calculate_kelly_criterion(self, strategy_name: str) -> float:
        """Calculate optimal position size using Kelly Criterion"""
        history = self.performance_history[strategy_name]
        
        if len(history) < self.min_sample_size:
            return 0.02  # Conservative 2% default
            
        # Calculate win probability and average win/loss
        wins = [h for h in history if h['profit'] > 0]
        losses = [h for h in history if h['profit'] <= 0]
        
        if not wins or not losses:
            return 0.02
            
        p = len(wins) / len(history)  # Win probability
        avg_win = np.mean([w['profit'] for w in wins])
        avg_loss = abs(np.mean([l['profit'] for l in losses]))
        
        b = avg_win / avg_loss  # Win/loss ratio
        
        # Kelly formula: f = (p * b - (1 - p)) / b
        kelly = (p * b - (1 - p)) / b
        
        # Apply Kelly fraction (usually 0.25 for safety)
        kelly *= 0.25
        
        # Cap at 10% for safety
        return min(kelly, 0.1)
        
    async def update_strategy_performance(self, strategy_name: str, trade_result: Dict):
        """Update strategy performance metrics"""
        if strategy_name not in self.strategies:
            return
            
        strategy = self.strategies[strategy_name]
        
        # Update performance history
        self.performance_history[strategy_name].append(trade_result)
        
        # Calculate updated metrics
        history = list(self.performance_history[strategy_name])
        
        if history:
            total_trades = len(history)
            successful_trades = sum(1 for t in history if t['profit'] > 0)
            total_profit = sum(t['profit'] for t in history)
            
            strategy.performance['trades'] = total_trades
            strategy.performance['success_rate'] = successful_trades / total_trades
            strategy.performance['roi'] = total_profit / sum(t['cost'] for t in history)
            
        # Trigger rebalancing if needed
        if total_trades % 50 == 0:  # Every 50 trades
            await self._rebalance_allocations()
            
    async def _rebalance_allocations(self):
        """Rebalance strategy allocations based on performance"""
        logger.info("Rebalancing strategy allocations...")
        
        # Calculate performance scores
        scores = {}
        for name, strategy in self.strategies.items():
            if strategy.performance['trades'] < self.min_sample_size:
                scores[name] = 1.0  # Neutral score for new strategies
            else:
                # Score based on ROI and success rate
                roi_score = 1 + strategy.performance['roi']
                success_score = strategy.performance['success_rate'] * 2
                scores[name] = roi_score * success_score
                
        # Normalize scores to allocations
        total_score = sum(scores.values())
        
        for name, score in scores.items():
            new_allocation = score / total_score
            
            # Apply limits (5% min, 40% max)
            new_allocation = max(0.05, min(0.4, new_allocation))
            
            old_allocation = self.strategies[name].allocation
            self.strategies[name].allocation = new_allocation
            
            if abs(new_allocation - old_allocation) > 0.05:
                logger.info(f"{name}: {old_allocation:.1%} -> {new_allocation:.1%}")
                
    async def _continuous_optimization(self):
        """Continuously optimize strategies"""
        while True:
            await asyncio.sleep(self.optimization_interval)
            
            try:
                # Optimize each strategy
                for name, strategy in self.strategies.items():
                    if strategy.performance['trades'] >= self.min_sample_size:
                        await self._optimize_strategy(name, strategy)
                        
                # Update market conditions
                await self._update_market_conditions()
                
                # Rebalance if needed
                await self._rebalance_allocations()
                
            except Exception as e:
                logger.error(f"Strategy optimization error: {e}")
                
    async def _optimize_strategy(self, name: str, strategy: Strategy):
        """Optimize individual strategy parameters"""
        history = list(self.performance_history[name])
        
        if not history:
            return
            
        # Analyze what works
        profitable_trades = [t for t in history if t['profit'] > 0]
        
        if name == 'pattern_arbitrage' and profitable_trades:
            # Identify most profitable patterns
            pattern_profits = defaultdict(list)
            for trade in profitable_trades:
                pattern = trade.get('pattern_index', -1)
                if pattern != -1:
                    pattern_profits[pattern].append(trade['profit_margin'])
                    
            # Update multipliers based on actual performance
            for pattern, profits in pattern_profits.items():
                if len(profits) >= 5:
                    avg_profit = np.mean(profits)
                    if pattern in strategy.parameters['target_patterns']:
                        old_multiplier = strategy.parameters['target_patterns'][pattern]['multiplier']
                        new_multiplier = old_multiplier * (1 + avg_profit)
                        strategy.parameters['target_patterns'][pattern]['multiplier'] = new_multiplier
                        
    async def _monitor_market_conditions(self):
        """Monitor and adapt to market conditions"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            
            try:
                conditions = await self._analyze_market_conditions()
                self.market_conditions = conditions
                
                # Adjust strategies based on conditions
                if conditions['volatility'] > 0.5:
                    # High volatility - reduce risk
                    self.risk_per_trade = 0.01
                    self.strategies['ai_momentum'].enabled = True
                else:
                    self.risk_per_trade = 0.02
                    
                if conditions['liquidity'] < 0.3:
                    # Low liquidity - disable market making
                    self.strategies['market_maker'].enabled = False
                else:
                    self.strategies['market_maker'].enabled = True
                    
            except Exception as e:
                logger.error(f"Market monitoring error: {e}")
                
    async def _analyze_market_conditions(self) -> Dict:
        """Analyze current market conditions"""
        # Placeholder - implement actual analysis
        return {
            'volatility': 0.3,
            'liquidity': 0.7,
            'trend': 'neutral',
            'volume': 'normal'
        }
        
    def _get_market_condition_multiplier(self, strategy_name: str) -> float:
        """Get multiplier based on market conditions"""
        if not self.market_conditions:
            return 1.0
            
        multiplier = 1.0
        
        # Adjust based on strategy and conditions
        if strategy_name == 'ai_momentum':
            if self.market_conditions.get('trend') == 'bullish':
                multiplier *= 1.5
            elif self.market_conditions.get('trend') == 'bearish':
                multiplier *= 0.5
                
        return multiplier
        
    async def _check_arbitrage(self, item_data: Dict) -> Dict:
        """Check cross-market arbitrage opportunities"""
        # Placeholder - implement actual arbitrage checking
        return {'margin': 0, 'markets': []}
        
    async def _calculate_momentum(self, item_data: Dict) -> float:
        """Calculate price momentum"""
        # Placeholder - implement momentum calculation
        return 0.0
        
    async def get_active_strategies(self) -> List[Dict]:
        """Get list of active strategies with stats"""
        active = []
        
        for name, strategy in self.strategies.items():
            if strategy.enabled:
                active.append({
                    'name': name,
                    'allocation': strategy.allocation,
                    'performance': strategy.performance,
                    'parameters': strategy.parameters
                })
                
        return active