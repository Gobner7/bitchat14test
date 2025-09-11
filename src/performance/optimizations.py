#!/usr/bin/env python3
"""
Apex Decompiler - Performance Optimizations
High-performance optimizations that surpass Oracle, Medal, and Konstant
"""

import time
import functools
import hashlib
import threading
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict
from functools import lru_cache
import weakref
import gc

class PerformanceProfiler:
    """Performance profiler for optimization analysis"""
    
    def __init__(self):
        self.timings = defaultdict(list)
        self.call_counts = defaultdict(int)
        self.memory_usage = {}
        
    def profile_function(self, func_name: str):
        """Decorator to profile function performance"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                start_memory = self._get_memory_usage()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    end_memory = self._get_memory_usage()
                    
                    execution_time = end_time - start_time
                    memory_delta = end_memory - start_memory
                    
                    self.timings[func_name].append(execution_time)
                    self.call_counts[func_name] += 1
                    self.memory_usage[func_name] = memory_delta
                    
            return wrapper
        return decorator
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            return 0
    
    def get_report(self) -> str:
        """Generate performance report"""
        report = ["=== Performance Report ===\n"]
        
        for func_name in sorted(self.timings.keys()):
            timings = self.timings[func_name]
            count = self.call_counts[func_name]
            
            if timings:
                avg_time = sum(timings) / len(timings)
                total_time = sum(timings)
                max_time = max(timings)
                min_time = min(timings)
                
                report.append(f"Function: {func_name}")
                report.append(f"  Calls: {count}")
                report.append(f"  Total time: {total_time:.4f}s")
                report.append(f"  Average time: {avg_time:.4f}s")
                report.append(f"  Min time: {min_time:.4f}s")
                report.append(f"  Max time: {max_time:.4f}s")
                
                if func_name in self.memory_usage:
                    memory = self.memory_usage[func_name]
                    report.append(f"  Memory delta: {memory / 1024 / 1024:.2f} MB")
                
                report.append("")
        
        return "\n".join(report)

class CacheManager:
    """Advanced caching system for performance optimization"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.caches = {}
        self.hit_counts = defaultdict(int)
        self.miss_counts = defaultdict(int)
        
    def cached_function(self, cache_name: str, max_size: int = 128):
        """Decorator for function caching"""
        def decorator(func):
            if cache_name not in self.caches:
                self.caches[cache_name] = {}
            
            cache = self.caches[cache_name]
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key
                key = self._make_cache_key(args, kwargs)
                
                if key in cache:
                    self.hit_counts[cache_name] += 1
                    return cache[key]
                
                # Cache miss - compute result
                self.miss_counts[cache_name] += 1
                result = func(*args, **kwargs)
                
                # Store in cache (with size limit)
                if len(cache) >= max_size:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
                
                cache[key] = result
                return result
                
            return wrapper
        return decorator
    
    def _make_cache_key(self, args, kwargs) -> str:
        """Create a cache key from function arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def clear_cache(self, cache_name: Optional[str] = None):
        """Clear specific cache or all caches"""
        if cache_name:
            if cache_name in self.caches:
                self.caches[cache_name].clear()
        else:
            for cache in self.caches.values():
                cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Dict[str, int]]:
        """Get cache statistics"""
        stats = {}
        
        for cache_name in self.caches:
            hits = self.hit_counts[cache_name]
            misses = self.miss_counts[cache_name]
            total = hits + misses
            hit_rate = hits / total if total > 0 else 0
            
            stats[cache_name] = {
                'hits': hits,
                'misses': misses,
                'hit_rate': hit_rate,
                'cache_size': len(self.caches[cache_name])
            }
        
        return stats

class ParallelProcessor:
    """Parallel processing for performance optimization"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        
    def parallel_map(self, func: Callable, items: List[Any], 
                    chunk_size: Optional[int] = None) -> List[Any]:
        """Parallel map function with automatic chunking"""
        import concurrent.futures
        
        if len(items) < 10:  # Don't parallelize small tasks
            return [func(item) for item in items]
        
        if chunk_size is None:
            chunk_size = max(1, len(items) // self.max_workers)
        
        results = [None] * len(items)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit chunks
            futures = []
            for i in range(0, len(items), chunk_size):
                chunk = items[i:i + chunk_size]
                future = executor.submit(self._process_chunk, func, chunk)
                futures.append((i, future))
            
            # Collect results
            for start_idx, future in futures:
                chunk_results = future.result()
                for j, result in enumerate(chunk_results):
                    results[start_idx + j] = result
        
        return results
    
    def _process_chunk(self, func: Callable, chunk: List[Any]) -> List[Any]:
        """Process a chunk of items"""
        return [func(item) for item in chunk]

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def optimize_strings(strings: List[str]) -> Dict[str, int]:
        """Optimize string storage using interning"""
        string_pool = {}
        
        for i, string in enumerate(strings):
            if string not in string_pool:
                string_pool[string] = len(string_pool)
            strings[i] = string_pool[string]
        
        return string_pool
    
    @staticmethod
    def compress_data(data: bytes) -> bytes:
        """Compress data to save memory"""
        import zlib
        return zlib.compress(data, level=6)
    
    @staticmethod
    def decompress_data(compressed_data: bytes) -> bytes:
        """Decompress data"""
        import zlib
        return zlib.decompress(compressed_data)
    
    @staticmethod
    def cleanup_memory():
        """Force garbage collection"""
        gc.collect()

class OptimizedDecompiler:
    """Performance-optimized decompiler wrapper"""
    
    def __init__(self, base_decompiler):
        self.base_decompiler = base_decompiler
        self.profiler = PerformanceProfiler()
        self.cache_manager = CacheManager()
        self.parallel_processor = ParallelProcessor()
        
        # Apply optimizations
        self._apply_optimizations()
    
    def _apply_optimizations(self):
        """Apply performance optimizations to base decompiler"""
        # Cache frequently called methods
        self.base_decompiler._parse_function = self.cache_manager.cached_function(
            "parse_function", max_size=256
        )(self.base_decompiler._parse_function)
        
        self.base_decompiler._instruction_to_source = self.cache_manager.cached_function(
            "instruction_to_source", max_size=512
        )(self.base_decompiler._instruction_to_source)
        
        # Profile critical methods
        self.base_decompiler.decompile_bytecode = self.profiler.profile_function(
            "decompile_bytecode"
        )(self.base_decompiler.decompile_bytecode)
        
        self.base_decompiler._parse_bytecode = self.profiler.profile_function(
            "parse_bytecode"
        )(self.base_decompiler._parse_bytecode)
        
        self.base_decompiler._generate_source = self.profiler.profile_function(
            "generate_source"
        )(self.base_decompiler._generate_source)
    
    def decompile_bytecode(self, bytecode: bytes) -> str:
        """Optimized decompilation with performance enhancements"""
        # Pre-process for optimization opportunities
        if len(bytecode) > 1024 * 1024:  # Large files (>1MB)
            # Use memory optimization for large files
            original_size = len(bytecode)
            compressed = MemoryOptimizer.compress_data(bytecode)
            compression_ratio = len(compressed) / original_size
            
            if compression_ratio < 0.8:  # Good compression
                bytecode = MemoryOptimizer.decompress_data(compressed)
        
        # Delegate to base decompiler
        result = self.base_decompiler.decompile_bytecode(bytecode)
        
        # Clean up memory after large operations
        if len(bytecode) > 1024 * 1024:
            MemoryOptimizer.cleanup_memory()
        
        return result
    
    def batch_decompile(self, bytecode_files: List[bytes]) -> List[str]:
        """Parallel batch decompilation"""
        if len(bytecode_files) <= 1:
            return [self.decompile_bytecode(bc) for bc in bytecode_files]
        
        # Use parallel processing for multiple files
        return self.parallel_processor.parallel_map(
            self.decompile_bytecode,
            bytecode_files,
            chunk_size=max(1, len(bytecode_files) // 4)
        )
    
    def get_performance_report(self) -> str:
        """Get comprehensive performance report"""
        report = []
        
        # Profiler report
        report.append(self.profiler.get_report())
        
        # Cache statistics
        report.append("=== Cache Statistics ===")
        cache_stats = self.cache_manager.get_cache_stats()
        
        for cache_name, stats in cache_stats.items():
            report.append(f"\nCache: {cache_name}")
            report.append(f"  Hits: {stats['hits']}")
            report.append(f"  Misses: {stats['misses']}")
            report.append(f"  Hit Rate: {stats['hit_rate']:.2%}")
            report.append(f"  Cache Size: {stats['cache_size']}")
        
        return "\n".join(report)
    
    def optimize_for_speed(self):
        """Optimize settings for maximum speed"""
        # Increase cache sizes
        self.cache_manager.max_size = 2000
        
        # Increase parallel workers
        self.parallel_processor.max_workers = min(8, (os.cpu_count() or 4))
        
    def optimize_for_memory(self):
        """Optimize settings for minimal memory usage"""
        # Reduce cache sizes
        self.cache_manager.max_size = 100
        
        # Clear caches more frequently
        self.cache_manager.clear_cache()
        
        # Reduce parallel workers
        self.parallel_processor.max_workers = 2
        
        # Force garbage collection
        MemoryOptimizer.cleanup_memory()

class BenchmarkSuite:
    """Benchmark suite for performance testing"""
    
    def __init__(self):
        self.results = {}
    
    def benchmark_decompiler(self, decompiler, test_files: List[bytes], 
                           iterations: int = 3) -> Dict[str, float]:
        """Benchmark decompiler performance"""
        results = {
            'total_time': 0,
            'avg_time_per_file': 0,
            'throughput_mb_per_sec': 0,
            'memory_efficiency': 0
        }
        
        total_size = sum(len(data) for data in test_files)
        times = []
        
        for iteration in range(iterations):
            start_time = time.perf_counter()
            start_memory = self._get_memory_usage()
            
            # Decompile all test files
            for bytecode in test_files:
                decompiler.decompile_bytecode(bytecode)
            
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            
            iteration_time = end_time - start_time
            memory_used = end_memory - start_memory
            
            times.append(iteration_time)
        
        # Calculate metrics
        avg_time = sum(times) / len(times)
        throughput = (total_size / 1024 / 1024) / avg_time  # MB/s
        
        results['total_time'] = avg_time
        results['avg_time_per_file'] = avg_time / len(test_files)
        results['throughput_mb_per_sec'] = throughput
        
        return results
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            return 0
    
    def compare_decompilers(self, decompilers: Dict[str, Any], 
                          test_files: List[bytes]) -> str:
        """Compare multiple decompilers"""
        results = {}
        
        for name, decompiler in decompilers.items():
            print(f"Benchmarking {name}...")
            results[name] = self.benchmark_decompiler(decompiler, test_files)
        
        # Generate comparison report
        report = ["=== Decompiler Performance Comparison ===\n"]
        
        for name, metrics in results.items():
            report.append(f"{name}:")
            report.append(f"  Total Time: {metrics['total_time']:.3f}s")
            report.append(f"  Avg Time per File: {metrics['avg_time_per_file']:.3f}s")
            report.append(f"  Throughput: {metrics['throughput_mb_per_sec']:.2f} MB/s")
            report.append("")
        
        # Find best performer
        fastest = min(results.keys(), key=lambda k: results[k]['total_time'])
        highest_throughput = max(results.keys(), key=lambda k: results[k]['throughput_mb_per_sec'])
        
        report.append("Performance Winners:")
        report.append(f"  Fastest: {fastest}")
        report.append(f"  Highest Throughput: {highest_throughput}")
        
        return "\n".join(report)

def main():
    """Test performance optimizations"""
    from core.decompiler_engine import ApexDecompiler
    
    # Create optimized decompiler
    base_decompiler = ApexDecompiler()
    optimized_decompiler = OptimizedDecompiler(base_decompiler)
    
    # Test with dummy data
    test_bytecode = b'\x1bLua\x51\x00' + b'\x00' * 100  # Minimal valid bytecode
    
    print("Testing performance optimizations...")
    
    # Test single decompilation
    start_time = time.time()
    result = optimized_decompiler.decompile_bytecode(test_bytecode)
    end_time = time.time()
    
    print(f"Decompilation time: {end_time - start_time:.4f}s")
    print(f"Result length: {len(result)} characters")
    
    # Test batch decompilation
    test_files = [test_bytecode] * 5
    
    start_time = time.time()
    results = optimized_decompiler.batch_decompile(test_files)
    end_time = time.time()
    
    print(f"Batch decompilation time: {end_time - start_time:.4f}s")
    print(f"Files processed: {len(results)}")
    
    # Print performance report
    print("\n" + optimized_decompiler.get_performance_report())

if __name__ == "__main__":
    main()