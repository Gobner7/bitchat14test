import time
import asyncio
from functools import wraps
from typing import Callable, Any, Dict
import psutil
import numpy as np
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import cProfile
import pstats
import io
from numba import jit
import uvloop

from .logger import perf_logger

# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class PerformanceMonitor:
    """Monitor and optimize performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'latency': deque(maxlen=1000),
            'cpu_usage': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'api_calls': deque(maxlen=1000),
            'websocket_messages': deque(maxlen=1000)
        }
        self.profiler = cProfile.Profile()
        
    def record_latency(self, operation: str, latency: float):
        """Record operation latency"""
        self.metrics['latency'].append({
            'operation': operation,
            'latency': latency,
            'timestamp': time.time()
        })
        
        if latency > 100:  # Log slow operations (>100ms)
            perf_logger.warning(f"Slow operation: {operation} took {latency:.2f}ms")
            
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.metrics['latency']:
            return {}
            
        latencies = [m['latency'] for m in self.metrics['latency']]
        
        return {
            'avg_latency': np.mean(latencies),
            'p50_latency': np.percentile(latencies, 50),
            'p95_latency': np.percentile(latencies, 95),
            'p99_latency': np.percentile(latencies, 99),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent
        }

# Global monitor instance
monitor = PerformanceMonitor()

def measure_latency(func: Callable) -> Callable:
    """Decorator to measure function latency"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            latency = (time.perf_counter() - start) * 1000
            monitor.record_latency(func.__name__, latency)
            
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            latency = (time.perf_counter() - start) * 1000
            monitor.record_latency(func.__name__, latency)
            
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

class OptimizedExecutor:
    """Optimized thread pool executor for CPU-bound tasks"""
    
    def __init__(self, max_workers: int):
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix='OptimizedWorker'
        )
        
        # Pre-warm threads
        for _ in range(max_workers):
            self.executor.submit(lambda: None)
            
    def submit(self, fn: Callable, *args, **kwargs):
        """Submit task with performance tracking"""
        def wrapped_fn():
            start = time.perf_counter()
            result = fn(*args, **kwargs)
            latency = (time.perf_counter() - start) * 1000
            monitor.record_latency(f"executor_{fn.__name__}", latency)
            return result
            
        return self.executor.submit(wrapped_fn)
        
    def shutdown(self):
        """Shutdown executor"""
        self.executor.shutdown(wait=False)

# JIT compiled functions for critical paths
@jit(nopython=True)
def calculate_profit_margin_fast(buy_price: float, sell_price: float, fee_rate: float = 0.13) -> float:
    """Ultra-fast profit margin calculation"""
    fees = (buy_price + sell_price) * fee_rate
    net_profit = sell_price - buy_price - fees
    return net_profit / buy_price if buy_price > 0 else 0

@jit(nopython=True)
def filter_profitable_items_fast(prices: np.ndarray, suggested_prices: np.ndarray, 
                                min_margin: float = 0.15) -> np.ndarray:
    """Fast filter for profitable items"""
    n = len(prices)
    profitable = np.zeros(n, dtype=np.bool_)
    
    for i in range(n):
        margin = calculate_profit_margin_fast(prices[i], suggested_prices[i])
        profitable[i] = margin >= min_margin
        
    return profitable

@jit(nopython=True)
def calculate_wear_value_fast(float_value: float) -> int:
    """Fast wear calculation"""
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

class BatchProcessor:
    """Process items in optimized batches"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.pending_items = []
        self.processor_task = None
        
    async def add_item(self, item: Any):
        """Add item to batch"""
        self.pending_items.append(item)
        
        if len(self.pending_items) >= self.batch_size:
            await self._process_batch()
            
    async def _process_batch(self):
        """Process accumulated batch"""
        if not self.pending_items:
            return
            
        batch = self.pending_items[:self.batch_size]
        self.pending_items = self.pending_items[self.batch_size:]
        
        # Process batch in parallel
        await self._parallel_process(batch)
        
    async def _parallel_process(self, batch: list):
        """Override this method in subclasses"""
        pass

async def profile_async_function(func: Callable, *args, **kwargs):
    """Profile an async function"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        result = await func(*args, **kwargs)
    finally:
        profiler.disable()
        
    # Get stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    perf_logger.debug(f"Profile for {func.__name__}:\n{s.getvalue()}")
    
    return result

def optimize_memory():
    """Optimize memory usage"""
    import gc
    
    # Force garbage collection
    gc.collect()
    
    # Get memory stats
    mem_info = psutil.Process().memory_info()
    perf_logger.info(f"Memory usage: {mem_info.rss / 1024 / 1024:.1f} MB")
    
    # Clear caches if memory usage is high
    if psutil.virtual_memory().percent > 80:
        perf_logger.warning("High memory usage detected, clearing caches")
        # Implement cache clearing logic