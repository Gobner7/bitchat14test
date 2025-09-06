import asyncio
import websockets
import json
import time
from typing import Dict, List, Callable, Optional, Set
from dataclasses import dataclass
import aiohttp
import ujson
import lz4.frame
from collections import deque
import hashlib
import random
from datetime import datetime
import ssl
import certifi
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from ..config import config
from ..utils.logger import get_logger
from ..utils.performance import measure_latency

logger = get_logger(__name__)

@dataclass
class WebSocketMessage:
    """Ultra-optimized message structure"""
    type: str
    data: Dict
    timestamp: float
    latency: float
    priority: int = 0

class UltraFastWebSocketManager:
    """Revolutionary WebSocket manager with microsecond latency"""
    
    def __init__(self):
        self.connections: List[websockets.WebSocketClientProtocol] = []
        self.message_queue = asyncio.Queue(maxsize=10000)
        self.priority_queue = asyncio.PriorityQueue(maxsize=1000)
        self.callbacks: Dict[str, List[Callable]] = {}
        self.active_connections: Set[str] = set()
        self.latency_stats = deque(maxlen=1000)
        self.ssl_context = self._create_ssl_context()
        self.executor = ThreadPoolExecutor(max_workers=config.sniper_threads)
        
        # Connection pooling for ultra-fast reconnects
        self.connection_pool = asyncio.Queue(maxsize=config.websocket_connections * 2)
        
        # Message deduplication
        self.seen_messages = deque(maxlen=10000)
        
        # Predictive caching
        self.predictive_cache = {}
        
        # Network optimization
        self.tcp_nodelay = True
        self.tcp_keepalive = True
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create optimized SSL context for minimal handshake time"""
        context = ssl.create_default_context(cafile=certifi.where())
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # For speed (use with caution)
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        return context
        
    async def connect(self):
        """Establish multiple WebSocket connections for redundancy and speed"""
        tasks = []
        for i in range(config.websocket_connections):
            task = asyncio.create_task(self._create_connection(i))
            tasks.append(task)
            
        await asyncio.gather(*tasks)
        
        # Start message processors
        asyncio.create_task(self._process_messages())
        asyncio.create_task(self._process_priority_messages())
        asyncio.create_task(self._monitor_latency())
        asyncio.create_task(self._predictive_prefetch())
        
        logger.info(f"Established {len(self.connections)} WebSocket connections")
        
    async def _create_connection(self, connection_id: int):
        """Create a single optimized WebSocket connection"""
        try:
            # Add random jitter to avoid detection
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            headers = self._get_stealth_headers()
            
            ws = await websockets.connect(
                config.ws_url,
                ssl=self.ssl_context,
                extra_headers=headers,
                compression=None,  # Disable for speed
                max_size=10**7,
                max_queue=1000,
                read_limit=2**20,
                write_limit=2**20,
                close_timeout=1,
                ping_interval=20,
                ping_timeout=10
            )
            
            # Set TCP options for minimal latency
            transport = ws.transport
            sock = transport.get_extra_info('socket')
            if sock:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
            self.connections.append(ws)
            self.active_connections.add(f"ws_{connection_id}")
            
            # Start listener
            asyncio.create_task(self._listen(ws, connection_id))
            
            # Subscribe to all events
            await self._subscribe_all(ws)
            
        except Exception as e:
            logger.error(f"Connection {connection_id} failed: {e}")
            await asyncio.sleep(1)
            asyncio.create_task(self._create_connection(connection_id))
            
    def _get_stealth_headers(self) -> Dict[str, str]:
        """Generate stealth headers to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        return {
            'User-Agent': random.choice(user_agents) if config.rotate_user_agents else user_agents[0],
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Authorization': f'Bearer {config.api_key}'
        }
        
    async def _subscribe_all(self, ws: websockets.WebSocketClientProtocol):
        """Subscribe to all relevant market events"""
        subscriptions = [
            {'type': 'subscribe', 'channel': 'listings.new'},
            {'type': 'subscribe', 'channel': 'listings.update'},
            {'type': 'subscribe', 'channel': 'listings.sold'},
            {'type': 'subscribe', 'channel': 'market.stats'},
            {'type': 'subscribe', 'channel': 'prices.update'},
            {'type': 'subscribe', 'channel': 'trades.completed'}
        ]
        
        for sub in subscriptions:
            await ws.send(ujson.dumps(sub))
            
    async def _listen(self, ws: websockets.WebSocketClientProtocol, connection_id: int):
        """Ultra-fast message listener with parallel processing"""
        try:
            async for message in ws:
                receive_time = time.perf_counter()
                
                # Fast decompression if needed
                if isinstance(message, bytes):
                    if message[:4] == b'LZ4\x00':
                        message = lz4.frame.decompress(message[4:])
                    message = message.decode('utf-8')
                
                # Ultra-fast JSON parsing
                data = ujson.loads(message)
                
                # Message deduplication
                msg_hash = hashlib.md5(message.encode()).hexdigest()
                if msg_hash in self.seen_messages:
                    continue
                self.seen_messages.append(msg_hash)
                
                # Calculate latency
                if 'timestamp' in data:
                    latency = receive_time - data['timestamp']
                else:
                    latency = 0
                
                # Create message object
                ws_message = WebSocketMessage(
                    type=data.get('type', 'unknown'),
                    data=data,
                    timestamp=receive_time,
                    latency=latency,
                    priority=self._calculate_priority(data)
                )
                
                # Route to appropriate queue
                if ws_message.priority > 5:
                    await self.priority_queue.put((10 - ws_message.priority, ws_message))
                else:
                    await self.message_queue.put(ws_message)
                    
                # Update latency stats
                self.latency_stats.append(latency)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Connection {connection_id} closed, reconnecting...")
            self.active_connections.remove(f"ws_{connection_id}")
            await self._create_connection(connection_id)
        except Exception as e:
            logger.error(f"Listen error on connection {connection_id}: {e}")
            
    def _calculate_priority(self, data: Dict) -> int:
        """Calculate message priority for ultra-fast processing"""
        priority = 0
        
        # New listing with good profit potential
        if data.get('type') == 'listing.new':
            price = data.get('price', float('inf'))
            suggested_price = data.get('suggested_price', price)
            if suggested_price > price * 1.2:
                priority = 10
            elif suggested_price > price * 1.1:
                priority = 8
                
        # Price drop
        elif data.get('type') == 'listing.update':
            if data.get('price_change', 0) < -0.05:
                priority = 7
                
        return priority
        
    async def _process_messages(self):
        """Process regular messages with parallel execution"""
        while True:
            try:
                message = await self.message_queue.get()
                
                # Execute callbacks in parallel
                if message.type in self.callbacks:
                    tasks = []
                    for callback in self.callbacks[message.type]:
                        task = asyncio.create_task(self._execute_callback(callback, message))
                        tasks.append(task)
                    
                    # Don't wait for completion to process next message
                    asyncio.gather(*tasks, return_exceptions=True)
                    
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                
    async def _process_priority_messages(self):
        """Process high-priority messages with extreme speed"""
        while True:
            try:
                _, message = await self.priority_queue.get()
                
                # Execute immediately in thread pool for maximum speed
                if message.type in self.callbacks:
                    for callback in self.callbacks[message.type]:
                        self.executor.submit(asyncio.run, callback(message))
                        
            except Exception as e:
                logger.error(f"Priority message processing error: {e}")
                
    async def _execute_callback(self, callback: Callable, message: WebSocketMessage):
        """Execute callback with error handling"""
        try:
            await callback(message)
        except Exception as e:
            logger.error(f"Callback error: {e}")
            
    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for specific event type"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
        
    async def _monitor_latency(self):
        """Monitor and optimize latency"""
        while True:
            await asyncio.sleep(10)
            
            if self.latency_stats:
                avg_latency = np.mean(self.latency_stats)
                p99_latency = np.percentile(self.latency_stats, 99)
                
                logger.info(f"WebSocket Latency - Avg: {avg_latency*1000:.2f}ms, P99: {p99_latency*1000:.2f}ms")
                
                # Auto-optimize if latency is high
                if avg_latency > 0.1:  # 100ms
                    await self._optimize_connections()
                    
    async def _optimize_connections(self):
        """Optimize connections for better latency"""
        logger.info("Optimizing WebSocket connections...")
        
        # Close slowest connections
        # Add more connections if needed
        if len(self.active_connections) < config.websocket_connections:
            for i in range(config.websocket_connections - len(self.active_connections)):
                asyncio.create_task(self._create_connection(len(self.connections) + i))
                
    async def _predictive_prefetch(self):
        """Predictive prefetching based on patterns"""
        while True:
            await asyncio.sleep(0.1)  # 100ms intervals
            
            # Implement predictive logic based on historical patterns
            # This is a placeholder for advanced ML-based prediction
            pass
            
    async def send_order(self, listing_id: str, price: float) -> Optional[Dict]:
        """Send order with microsecond precision"""
        start_time = time.perf_counter()
        
        order_data = {
            'type': 'order.create',
            'listing_id': listing_id,
            'price': price,
            'timestamp': time.time(),
            'nonce': random.randint(1000000, 9999999)
        }
        
        # Send to multiple connections for redundancy
        tasks = []
        for ws in self.connections[:3]:  # Use first 3 connections
            if ws.open:
                task = asyncio.create_task(ws.send(ujson.dumps(order_data)))
                tasks.append(task)
                
        await asyncio.gather(*tasks, return_exceptions=True)
        
        latency = (time.perf_counter() - start_time) * 1000
        logger.info(f"Order sent in {latency:.2f}ms")
        
        return order_data
        
    async def close(self):
        """Close all connections gracefully"""
        for ws in self.connections:
            await ws.close()
        self.executor.shutdown(wait=False)