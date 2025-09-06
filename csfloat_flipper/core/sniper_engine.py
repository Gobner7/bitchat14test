import asyncio
import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import numpy as np
from collections import defaultdict
import hashlib
import random

from ..config import config
from ..utils.logger import get_logger
from ..utils.performance import measure_latency, OptimizedExecutor
from .websocket_manager import UltraFastWebSocketManager
from .ai_predictor import AdvancedAIPredictor

logger = get_logger(__name__)

@dataclass
class SnipeTarget:
    """Optimized snipe target data structure"""
    listing_id: str
    price: float
    predicted_price: float
    profit_margin: float
    confidence: float
    priority: int
    timestamp: float
    item_data: Dict

class UltraFastSniper:
    """Revolutionary sniping engine with microsecond reaction times"""
    
    def __init__(self, ws_manager: UltraFastWebSocketManager, predictor: AdvancedAIPredictor):
        self.ws_manager = ws_manager
        self.predictor = predictor
        
        # Multi-threaded execution for parallel sniping
        self.executor = ThreadPoolExecutor(max_workers=config.sniper_threads)
        self.optimized_executor = OptimizedExecutor(config.sniper_threads * 2)
        
        # Snipe queues with priority
        self.snipe_queue = asyncio.PriorityQueue(maxsize=1000)
        self.instant_snipe_queue = asyncio.Queue(maxsize=100)
        
        # Tracking
        self.active_snipes: Set[str] = set()
        self.completed_snipes: Dict[str, Dict] = {}
        self.snipe_stats = defaultdict(int)
        
        # Performance optimization
        self.session_pool: List[aiohttp.ClientSession] = []
        self.dns_cache = {}
        
        # Anti-pattern detection
        self.snipe_history = []
        self.cooldown_items: Set[str] = set()
        
        # Pre-computed decisions
        self.decision_cache = {}
        
        # Initialize
        asyncio.create_task(self._initialize())
        
    async def _initialize(self):
        """Initialize sniper with optimizations"""
        # Create session pool for parallel requests
        for _ in range(config.sniper_threads):
            session = await self._create_optimized_session()
            self.session_pool.append(session)
            
        # Register WebSocket callbacks
        self.ws_manager.register_callback('listing.new', self._on_new_listing)
        self.ws_manager.register_callback('listing.update', self._on_listing_update)
        
        # Start snipe processors
        for i in range(config.worker_threads):
            asyncio.create_task(self._process_snipe_queue())
            
        for i in range(4):  # 4 instant snipe processors
            asyncio.create_task(self._process_instant_snipes())
            
        # Start monitoring
        asyncio.create_task(self._monitor_performance())
        asyncio.create_task(self._optimize_strategies())
        
        logger.info(f"Sniper initialized with {config.sniper_threads} threads")
        
    async def _create_optimized_session(self) -> aiohttp.ClientSession:
        """Create hyper-optimized HTTP session"""
        connector = aiohttp.TCPConnector(
            limit=1000,
            limit_per_host=100,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
            force_close=False,
            keepalive_timeout=30,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=5,
            connect=0.5,
            sock_connect=0.5,
            sock_read=2
        )
        
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Authorization': f'Bearer {config.api_key}'
        }
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            json_serialize=ujson.dumps
        )
        
    async def _on_new_listing(self, message):
        """Ultra-fast new listing handler"""
        try:
            listing_data = message.data
            
            # Instant pre-filter for speed
            if not self._quick_filter(listing_data):
                return
                
            # Check if already processing
            listing_id = listing_data.get('id')
            if listing_id in self.active_snipes:
                return
                
            self.active_snipes.add(listing_id)
            
            # Parallel analysis
            analysis_task = asyncio.create_task(self._analyze_listing(listing_data))
            
            # Pre-emptive bid preparation
            if self._is_instant_snipe_candidate(listing_data):
                await self.instant_snipe_queue.put(listing_data)
            else:
                # Wait for analysis
                snipe_target = await analysis_task
                if snipe_target:
                    priority = 10 - snipe_target.priority
                    await self.snipe_queue.put((priority, snipe_target))
                    
        except Exception as e:
            logger.error(f"New listing handler error: {e}")
            
    def _quick_filter(self, listing: Dict) -> bool:
        """Ultra-fast pre-filtering"""
        price = listing.get('price', float('inf'))
        
        # Quick checks
        if price < config.item_filters['min_price'] or price > config.item_filters['max_price']:
            return False
            
        if config.item_filters['exclude_souvenir'] and listing.get('souvenir'):
            return False
            
        # Weapon type filter
        weapon = listing.get('weapon_type', '').lower()
        if weapon and weapon not in config.item_filters['weapon_types']:
            return False
            
        return True
        
    def _is_instant_snipe_candidate(self, listing: Dict) -> bool:
        """Identify instant snipe opportunities"""
        price = listing.get('price', float('inf'))
        suggested_price = listing.get('suggested_price', price)
        
        # Instant snipe if underpriced by 30%+
        if suggested_price > price * 1.3:
            return True
            
        # Known profitable patterns
        pattern_index = listing.get('pattern_index', -1)
        if pattern_index in [661, 670, 321, 387, 179, 555]:  # High-tier patterns
            if price < listing.get('avg_price', price) * 0.8:
                return True
                
        # Low float premium items
        float_value = listing.get('float_value', 1)
        if float_value < 0.0001 and price < suggested_price * 0.9:
            return True
            
        return False
        
    async def _analyze_listing(self, listing: Dict) -> Optional[SnipeTarget]:
        """Comprehensive listing analysis"""
        try:
            start_time = time.perf_counter()
            
            # Get AI prediction
            prediction = await self.predictor.predict_price(listing)
            
            price = listing.get('price', 0)
            predicted_price = prediction['predicted_price']
            confidence = prediction['confidence']
            
            # Calculate profit potential
            fees = price * 0.13  # Steam + CSFloat fees
            net_profit = predicted_price - price - fees
            profit_margin = net_profit / price if price > 0 else 0
            
            # Check if profitable
            if profit_margin < config.min_profit_margin:
                return None
                
            # Advanced profitability checks
            if not await self._advanced_profitability_check(listing, prediction):
                return None
                
            # Calculate priority
            priority = self._calculate_snipe_priority(
                profit_margin, confidence, listing
            )
            
            analysis_time = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Analysis completed in {analysis_time:.2f}ms")
            
            return SnipeTarget(
                listing_id=listing.get('id'),
                price=price,
                predicted_price=predicted_price,
                profit_margin=profit_margin,
                confidence=confidence,
                priority=priority,
                timestamp=time.time(),
                item_data=listing
            )
            
        except Exception as e:
            logger.error(f"Listing analysis error: {e}")
            return None
            
    async def _advanced_profitability_check(self, listing: Dict, prediction: Dict) -> bool:
        """Advanced profitability validation"""
        # Check market liquidity
        liquidity = await self._check_liquidity(listing)
        if liquidity < config.item_filters['min_liquidity_score']:
            return False
            
        # Check price history volatility
        volatility = await self._check_volatility(listing)
        if volatility > 0.5:  # Too volatile
            return False
            
        # Cross-market arbitrage check
        if config.strategies['cross_market_arbitrage']['enabled']:
            arbitrage = await self._check_arbitrage_opportunity(listing)
            if arbitrage['profitable']:
                return True
                
        return True
        
    def _calculate_snipe_priority(self, profit_margin: float, confidence: float, 
                                  listing: Dict) -> int:
        """Calculate snipe priority (0-10, 10 being highest)"""
        priority = 5  # Base priority
        
        # Profit margin factor
        if profit_margin > 0.5:
            priority += 3
        elif profit_margin > 0.3:
            priority += 2
        elif profit_margin > 0.2:
            priority += 1
            
        # Confidence factor
        if confidence > 0.9:
            priority += 2
        elif confidence > 0.8:
            priority += 1
            
        # Special items
        if listing.get('sticker_value', 0) > 100:
            priority += 1
            
        if listing.get('float_value', 1) < 0.001:
            priority += 1
            
        return min(priority, 10)
        
    async def _process_snipe_queue(self):
        """Process regular snipe queue"""
        while True:
            try:
                _, target = await self.snipe_queue.get()
                
                # Check if still valid
                if time.time() - target.timestamp > 10:  # 10 second timeout
                    continue
                    
                # Execute snipe
                asyncio.create_task(self._execute_snipe(target))
                
            except Exception as e:
                logger.error(f"Snipe queue processing error: {e}")
                
    async def _process_instant_snipes(self):
        """Process instant snipe opportunities with maximum speed"""
        while True:
            try:
                listing = await self.instant_snipe_queue.get()
                
                # Ultra-fast execution
                self.optimized_executor.submit(
                    self._execute_instant_snipe, listing
                )
                
            except Exception as e:
                logger.error(f"Instant snipe processing error: {e}")
                
    async def _execute_snipe(self, target: SnipeTarget):
        """Execute snipe with all optimizations"""
        start_time = time.perf_counter()
        
        try:
            # Get fastest session
            session = self._get_fastest_session()
            
            # Prepare request
            url = f"{config.base_url}/listings/{target.listing_id}/buy"
            
            data = {
                'price': target.price,
                'listing_id': target.listing_id,
                'timestamp': time.time(),
                'nonce': random.randint(1000000, 9999999)
            }
            
            # Execute with retry
            success = False
            for attempt in range(3):
                try:
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            success = True
                            break
                        elif response.status == 409:  # Already sold
                            break
                            
                except asyncio.TimeoutError:
                    if attempt < 2:
                        await asyncio.sleep(0.05)  # 50ms retry delay
                        
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Log result
            if success:
                logger.info(f"✅ Snipe successful! {target.listing_id} - "
                           f"Profit: ${target.profit_margin * target.price:.2f} - "
                           f"Time: {execution_time:.2f}ms")
                self.snipe_stats['successful'] += 1
            else:
                logger.info(f"❌ Snipe failed: {target.listing_id} - "
                           f"Time: {execution_time:.2f}ms")
                self.snipe_stats['failed'] += 1
                
            # Track for analysis
            self.completed_snipes[target.listing_id] = {
                'success': success,
                'execution_time': execution_time,
                'profit_margin': target.profit_margin,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Snipe execution error: {e}")
        finally:
            self.active_snipes.discard(target.listing_id)
            
    async def _execute_instant_snipe(self, listing: Dict):
        """Execute instant snipe with microsecond precision"""
        start_time = time.perf_counter()
        
        try:
            # Use WebSocket for ultra-fast order
            order_data = await self.ws_manager.send_order(
                listing.get('id'),
                listing.get('price')
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            logger.info(f"⚡ Instant snipe executed in {execution_time:.2f}ms")
            self.snipe_stats['instant'] += 1
            
        except Exception as e:
            logger.error(f"Instant snipe error: {e}")
            
    def _get_fastest_session(self) -> aiohttp.ClientSession:
        """Get session with lowest latency"""
        # Simple round-robin for now
        # Could implement latency tracking
        return random.choice(self.session_pool)
        
    def _get_random_user_agent(self) -> str:
        """Get random user agent for stealth"""
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return random.choice(agents)
        
    async def _check_liquidity(self, listing: Dict) -> float:
        """Check item liquidity score"""
        # Implement liquidity calculation based on:
        # - Number of recent sales
        # - Average time to sell
        # - Number of active listings
        return 0.8  # Placeholder
        
    async def _check_volatility(self, listing: Dict) -> float:
        """Check price volatility"""
        # Implement volatility calculation
        return 0.2  # Placeholder
        
    async def _check_arbitrage_opportunity(self, listing: Dict) -> Dict:
        """Check cross-market arbitrage"""
        # Implement arbitrage detection
        return {'profitable': False, 'margin': 0}
        
    async def _monitor_performance(self):
        """Monitor sniper performance"""
        while True:
            await asyncio.sleep(60)  # Every minute
            
            total = sum(self.snipe_stats.values())
            if total > 0:
                success_rate = self.snipe_stats['successful'] / total
                logger.info(f"Sniper Stats - Total: {total}, Success Rate: {success_rate:.2%}, "
                           f"Instant: {self.snipe_stats['instant']}")
                
    async def _optimize_strategies(self):
        """Continuously optimize sniping strategies"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            
            # Analyze recent performance
            recent_snipes = [s for s in self.completed_snipes.values() 
                           if time.time() - s['timestamp'] < 3600]
            
            if recent_snipes:
                # Adjust parameters based on performance
                avg_success = sum(s['success'] for s in recent_snipes) / len(recent_snipes)
                
                if avg_success < 0.5:
                    # Increase minimum profit margin if success rate is low
                    config.min_profit_margin *= 1.1
                    logger.info(f"Adjusted min profit margin to {config.min_profit_margin:.2%}")
                    
    async def close(self):
        """Cleanup resources"""
        for session in self.session_pool:
            await session.close()
        self.executor.shutdown(wait=False)
        self.optimized_executor.shutdown()